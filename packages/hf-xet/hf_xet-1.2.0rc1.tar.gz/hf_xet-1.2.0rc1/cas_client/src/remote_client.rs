use std::collections::HashMap;
use std::io::Write;
use std::mem::take;
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};

use anyhow::anyhow;
use bytes::Bytes;
use cas_object::SerializedCasObject;
use cas_types::{
    BatchQueryReconstructionResponse, CASReconstructionTerm, ChunkRange, FileRange, HttpRange, Key,
    QueryReconstructionResponse, UploadShardResponse, UploadShardResponseType, UploadXorbResponse,
};
use chunk_cache::{CacheConfig, ChunkCache};
use error_printer::ErrorPrinter;
use http::HeaderValue;
use http::header::{CONTENT_LENGTH, RANGE};
use mdb_shard::file_structs::{FileDataSequenceEntry, FileDataSequenceHeader, MDBFileInfo};
use merklehash::MerkleHash;
use progress_tracking::item_tracking::SingleItemProgressUpdater;
use progress_tracking::upload_tracking::CompletionTracker;
use reqwest::{Body, Response, StatusCode, Url};
use reqwest_middleware::ClientWithMiddleware;
use tokio::sync::{OwnedSemaphorePermit, mpsc};
use tokio::task::{JoinHandle, JoinSet};
use tracing::{debug, info, instrument};
use utils::auth::AuthConfig;
#[cfg(not(target_family = "wasm"))]
use utils::singleflight::Group;
use xet_runtime::{GlobalSemaphoreHandle, XetRuntime, global_semaphore_handle};

#[cfg(not(target_family = "wasm"))]
use crate::download_utils::*;
use crate::error::{CasClientError, Result};
use crate::http_client::{Api, ResponseErrorLogger, RetryConfig};
#[cfg(not(target_family = "wasm"))]
use crate::output_provider::OutputProvider;
use crate::retry_wrapper::RetryWrapper;
use crate::{Client, http_client};

pub const CAS_ENDPOINT: &str = "http://localhost:8080";
pub const PREFIX_DEFAULT: &str = "default";

utils::configurable_constants! {
    /// Env (HF_XET_NUM_CONCURRENT_RANGE_GETS) to set the number of concurrent range gets.
    /// setting this value to 0 disables the limit, sets it to the max, this is not recommended as it may lead to errors
    ref NUM_CONCURRENT_RANGE_GETS: usize = GlobalConfigMode::HighPerformanceOption {
        standard: 48,
        high_performance: 256,
    };

    /// Send a report of successful partial upload every 512kb.
    ref UPLOAD_REPORTING_BLOCK_SIZE : usize = 512 * 1024;

    /// Env (HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY) to switch to writing terms sequentially to disk.
    /// Benchmarks have shown that on SSD machines, writing in parallel seems to far outperform
    /// sequential term writes.
    /// However, this is not likely the case for writing to HDD and may in fact be worse,
    /// so for those machines, setting this env may help download perf.
    ref RECONSTRUCT_WRITE_SEQUENTIALLY : bool = false;

}

lazy_static! {
    static ref DOWNLOAD_CHUNK_RANGE_CONCURRENCY_LIMITER: GlobalSemaphoreHandle =
        global_semaphore_handle!(*NUM_CONCURRENT_RANGE_GETS);
    static ref FN_CALL_ID: AtomicU64 = AtomicU64::new(1);
}

pub struct RemoteClient {
    endpoint: String,
    dry_run: bool,
    http_client_with_retry: Arc<ClientWithMiddleware>,
    authenticated_http_client_with_retry: Arc<ClientWithMiddleware>,
    authenticated_http_client: Arc<ClientWithMiddleware>,
    chunk_cache: Option<Arc<dyn ChunkCache>>,
    #[cfg(not(target_family = "wasm"))]
    range_download_single_flight: RangeDownloadSingleFlight,
    shard_cache_directory: Option<PathBuf>,
}

pub(crate) async fn get_reconstruction_with_endpoint_and_client(
    endpoint: &str,
    client: &ClientWithMiddleware,
    file_hash: &MerkleHash,
    byte_range: Option<FileRange>,
) -> Result<Option<QueryReconstructionResponse>> {
    let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
    let url = Url::parse(&format!("{endpoint}/reconstructions/{}", file_hash.hex()))?;
    info!(
        call_id,
        %file_hash,
        ?byte_range,
        "Starting get_reconstruction API call",
    );

    let mut request = client.get(url).with_extension(Api("cas::get_reconstruction"));
    if let Some(range) = byte_range {
        // convert exclusive-end to inclusive-end range
        request = request.header(RANGE, HttpRange::from(range).range_header())
    }
    let response = request.send().await.process_error("get_reconstruction");

    let Ok(response) = response else {
        let e = response.unwrap_err();

        // bytes_range not satisfiable
        if let CasClientError::ReqwestError(e, _) = &e
            && let Some(StatusCode::RANGE_NOT_SATISFIABLE) = e.status()
        {
            return Ok(None);
        }

        return Err(e);
    };

    let len = response.content_length();
    info!(%file_hash, len, "query_reconstruction");

    let query_reconstruction_response: QueryReconstructionResponse = response
        .json()
        .await
        .info_error_fn(|| format!("JSON parsing failed in get_reconstruction, call_id={}", call_id))?;

    info!(
        call_id,
        %file_hash,
        ?byte_range,
        "Completed get_reconstruction API call"
    );

    Ok(Some(query_reconstruction_response))
}

#[cfg(not(target_family = "wasm"))]
#[allow(clippy::too_many_arguments)]
pub(crate) async fn map_fetch_info_into_download_tasks(
    segment: Arc<FetchInfo>,
    terms: Vec<CASReconstructionTerm>,
    offset_into_first_range: u64,
    base_write_negative_offset: u64,
    chunk_cache: Option<Arc<dyn ChunkCache>>,
    client: Arc<ClientWithMiddleware>,
    range_download_single_flight: Arc<Group<DownloadRangeResult, CasClientError>>,
    output_provider: &OutputProvider,
) -> Result<Vec<FetchTermDownloadOnceAndWriteEverywhereUsed>> {
    // the actual segment length.
    // the file_range end may actually exceed the file total length for the last segment.
    // in that case, the maximum length of this segment will be the total of all terms given
    //  minus the start offset
    let seg_len = segment
        .file_range
        .length()
        .min(terms.iter().fold(0, |acc, term| acc + term.unpacked_length as u64) - offset_into_first_range);

    let initial_writer_offset = segment.file_range.start - base_write_negative_offset;
    let mut total_taken = 0;

    let mut fetch_info_term_map: HashMap<(MerkleHash, ChunkRange), FetchTermDownloadOnceAndWriteEverywhereUsed> =
        HashMap::new();
    for (i, term) in terms.into_iter().enumerate() {
        let (individual_fetch_info, _) = segment.find((term.hash, term.range)).await?;

        let skip_bytes = if i == 0 { offset_into_first_range } else { 0 };
        // amount to take is min of the whole term after skipped bytes or the remainder of the segment
        let take = (term.unpacked_length as u64 - skip_bytes).min(seg_len - total_taken);
        let write_term = ChunkRangeWrite {
            // term details
            chunk_range: term.range,
            unpacked_length: term.unpacked_length,

            // write details
            skip_bytes,
            take,
            writer_offset: initial_writer_offset + total_taken,
        };

        let task = fetch_info_term_map
            .entry((term.hash.into(), individual_fetch_info.range))
            .or_insert_with(|| FetchTermDownloadOnceAndWriteEverywhereUsed {
                download: FetchTermDownload {
                    hash: term.hash.into(),
                    range: individual_fetch_info.range,
                    fetch_info: segment.clone(),
                    chunk_cache: chunk_cache.clone(),
                    client: client.clone(),
                    range_download_single_flight: range_download_single_flight.clone(),
                },
                writes: vec![],
                output: output_provider.clone(),
            });
        task.writes.push(write_term);

        total_taken += take;
    }

    let tasks = fetch_info_term_map.into_values().collect();

    Ok(tasks)
}

impl RemoteClient {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        endpoint: &str,
        auth: &Option<AuthConfig>,
        cache_config: &Option<CacheConfig>,
        shard_cache_directory: Option<PathBuf>,
        session_id: &str,
        dry_run: bool,
    ) -> Self {
        // use disk cache if cache_config provided.
        let chunk_cache = if let Some(cache_config) = cache_config {
            if cache_config.cache_size == 0 {
                info!("Chunk cache size set to 0, disabling chunk cache");
                None
            } else {
                info!(cache.dir=?cache_config.cache_directory, cache.size=cache_config.cache_size,"Using disk cache");
                chunk_cache::get_cache(cache_config)
                    .log_error("failed to initialize cache, not using cache")
                    .ok()
            }
        } else {
            None
        };

        Self {
            endpoint: endpoint.to_string(),
            dry_run,
            authenticated_http_client_with_retry: Arc::new(
                http_client::build_auth_http_client(auth, RetryConfig::default(), session_id).unwrap(),
            ),
            authenticated_http_client: Arc::new(
                http_client::build_auth_http_client_no_retry(auth, session_id).unwrap(),
            ),
            http_client_with_retry: Arc::new(
                http_client::build_http_client(RetryConfig::default(), session_id).unwrap(),
            ),
            chunk_cache,
            #[cfg(not(target_family = "wasm"))]
            range_download_single_flight: Arc::new(Group::new()),
            shard_cache_directory,
        }
    }

    async fn query_dedup_api(&self, prefix: &str, chunk_hash: &MerkleHash) -> Result<Option<Response>> {
        // The API endpoint now only supports non-batched dedup request and
        let key = Key {
            prefix: prefix.into(),
            hash: *chunk_hash,
        };

        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        let url = Url::parse(&format!("{}/chunks/{key}", self.endpoint))?;
        info!(
            call_id,
            prefix,
            %chunk_hash,
            "Starting query_dedup API call",
        );

        let client = self.authenticated_http_client.clone();
        let api_tag = "cas::query_dedup";

        let result = RetryWrapper::new(api_tag)
            .with_429_no_retry()
            .log_errors_as_info()
            .run(move || client.get(url.clone()).with_extension(Api(api_tag)).send())
            .await;

        if result.as_ref().is_err_and(|e| e.status().is_some()) {
            info!(
                call_id,
                prefix,
                %chunk_hash,
                result="not_found",
                "Completed query_dedup API call",
            );
            return Ok(None);
        }

        info!(
            call_id,
            prefix,
            %chunk_hash,
            result="found",
            "Completed query_dedup API call",
        );
        Ok(Some(result?))
    }
}

#[cfg(not(target_family = "wasm"))]
impl RemoteClient {
    #[instrument(skip_all, name = "RemoteClient::batch_get_reconstruction")]
    async fn batch_get_reconstruction(
        &self,
        file_ids: impl Iterator<Item = &MerkleHash>,
    ) -> Result<BatchQueryReconstructionResponse> {
        let mut url_str = format!("{}/reconstructions?", self.endpoint);
        let mut is_first = true;
        let mut file_id_list = Vec::new();
        for hash in file_ids {
            file_id_list.push(hash.hex());
            if is_first {
                is_first = false;
            } else {
                url_str.push('&');
            }
            url_str.push_str("file_id=");
            url_str.push_str(hash.hex().as_str());
        }
        let url: Url = url_str.parse()?;

        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        info!(call_id, file_ids=?file_id_list, "Starting batch_get_reconstruction API call");

        let api_tag = "cas::batch_get_reconstruction";
        let client = self.authenticated_http_client.clone();

        let response: BatchQueryReconstructionResponse = RetryWrapper::new(api_tag)
            .run_and_extract_json(move || client.get(url.clone()).with_extension(Api(api_tag)).send())
            .await?;

        info!(call_id,
            file_ids=?file_id_list,
            response_count=response.files.len(),
            "Completed batch_get_reconstruction API call",
        );

        Ok(response)
    }

    // Segmented download such that the file reconstruction and fetch info is not queried in its entirety
    // at the beginning of the download, but queried in segments. Range downloads are executed with
    // a certain degree of parallelism, but writing out to storage is sequential. Ideal when the external
    // storage uses HDDs.
    #[instrument(skip_all, name = "RemoteClient::reconstruct_file_segmented", fields(file.hash = file_hash.hex()
    ))]
    async fn reconstruct_file_to_writer_segmented(
        &self,
        file_hash: &MerkleHash,
        byte_range: Option<FileRange>,
        writer: &OutputProvider,
        progress_updater: Option<Arc<SingleItemProgressUpdater>>,
    ) -> Result<u64> {
        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        info!(
            call_id,
            %file_hash,
            ?byte_range,
            "Starting reconstruct_file_to_writer_segmented",
        );

        // Use an unlimited queue size, as queue size is inherently bounded by degree of concurrency.
        let (task_tx, mut task_rx) = mpsc::unbounded_channel::<DownloadQueueItem<SequentialTermDownload>>();
        let (running_downloads_tx, mut running_downloads_rx) =
            mpsc::unbounded_channel::<JoinHandle<Result<(TermDownloadResult<Vec<u8>>, OwnedSemaphorePermit)>>>();

        // derive the actual range to reconstruct
        let file_reconstruct_range = byte_range.unwrap_or_else(FileRange::full);
        let total_len = file_reconstruct_range.length();

        // kick-start the download by enqueue the fetch info task.
        task_tx.send(DownloadQueueItem::Metadata(FetchInfo::new(
            *file_hash,
            file_reconstruct_range,
            self.endpoint.clone(),
            self.authenticated_http_client_with_retry.clone(),
        )))?;

        // Start the queue processing logic
        //
        // If the queue item is `DownloadQueueItem::Metadata`, it fetches the file reconstruction info
        // of the first segment, whose size is linear to `num_concurrent_range_gets`. Once fetched, term
        // download tasks are enqueued and spawned with the degree of concurrency equal to `num_concurrent_range_gets`.
        // After the above, a task that defines fetching the remainder of the file reconstruction info is enqueued,
        // which will execute after the first of the above term download tasks finishes.
        let chunk_cache = self.chunk_cache.clone();
        let term_download_client = self.http_client_with_retry.clone();
        let range_download_single_flight = self.range_download_single_flight.clone();
        let download_scheduler = DownloadSegmentLengthTuner::from_configurable_constants();
        let download_scheduler_clone = download_scheduler.clone();

        let download_concurrency_limiter =
            XetRuntime::current().global_semaphore(*DOWNLOAD_CHUNK_RANGE_CONCURRENCY_LIMITER);

        info!(concurrency_limit = *NUM_CONCURRENT_RANGE_GETS, "Starting segmented download");

        let queue_dispatcher: JoinHandle<Result<()>> = tokio::spawn(async move {
            let mut remaining_total_len = total_len;
            while let Some(item) = task_rx.recv().await {
                match item {
                    DownloadQueueItem::End => {
                        // everything processed
                        debug!(call_id, "download queue emptied");
                        drop(running_downloads_tx);
                        break;
                    },
                    DownloadQueueItem::DownloadTask(term_download) => {
                        // acquire the permit before spawning the task, so that there's limited
                        // number of active downloads.
                        let permit = download_concurrency_limiter.clone().acquire_owned().await?;
                        debug!(call_id, "spawning 1 download task");
                        let future: JoinHandle<Result<(TermDownloadResult<Vec<u8>>, OwnedSemaphorePermit)>> =
                            tokio::spawn(async move {
                                let data = term_download.run().await?;
                                Ok((data, permit))
                            });
                        running_downloads_tx.send(future)?;
                    },
                    DownloadQueueItem::Metadata(fetch_info) => {
                        // query for the file info of the first segment
                        let segment_size = download_scheduler_clone.next_segment_size()?;
                        debug!(call_id, segment_size, "querying file info");
                        let (segment, maybe_remainder) = fetch_info.take_segment(segment_size);

                        let Some((offset_into_first_range, terms)) = segment.query().await? else {
                            // signal termination
                            task_tx.send(DownloadQueueItem::End)?;
                            continue;
                        };

                        let segment = Arc::new(segment);
                        // define the term download tasks
                        let mut remaining_segment_len = segment_size;
                        debug!(call_id, num_tasks = terms.len(), "enqueueing download tasks");
                        for (i, term) in terms.into_iter().enumerate() {
                            let skip_bytes = if i == 0 { offset_into_first_range } else { 0 };
                            let take = remaining_total_len
                                .min(remaining_segment_len)
                                .min(term.unpacked_length as u64 - skip_bytes);
                            let (individual_fetch_info, _) = segment.find((term.hash, term.range)).await?;

                            let download_task = SequentialTermDownload {
                                download: FetchTermDownload {
                                    hash: term.hash.into(),
                                    range: individual_fetch_info.range,
                                    fetch_info: segment.clone(),
                                    chunk_cache: chunk_cache.clone(),
                                    client: term_download_client.clone(),
                                    range_download_single_flight: range_download_single_flight.clone(),
                                },
                                term,
                                skip_bytes,
                                take,
                            };

                            remaining_total_len -= take;
                            remaining_segment_len -= take;
                            debug!(call_id, ?download_task, "enqueueing task");
                            task_tx.send(DownloadQueueItem::DownloadTask(download_task))?;
                        }

                        // enqueue the remainder of file info fetch task
                        if let Some(remainder) = maybe_remainder {
                            task_tx.send(DownloadQueueItem::Metadata(remainder))?;
                        } else {
                            task_tx.send(DownloadQueueItem::End)?;
                        }
                    },
                }
            }

            Ok(())
        });

        let mut writer = writer.get_writer_at(0)?;
        let mut total_written = 0;
        while let Some(result) = running_downloads_rx.recv().await {
            match result.await {
                Ok(Ok((mut download_result, permit))) => {
                    let data = take(&mut download_result.payload);
                    writer.write_all(&data)?;
                    // drop permit after data written out so they don't accumulate in memory unbounded
                    drop(permit);

                    if let Some(updater) = progress_updater.as_ref() {
                        updater.update(data.len() as u64).await;
                    }

                    total_written += data.len() as u64;

                    // Now inspect the download metrics and tune the download degree of concurrency
                    download_scheduler.tune_on(download_result)?;
                },
                Ok(Err(e)) => Err(e)?,
                Err(e) => Err(anyhow!("{e:?}"))?,
            }
        }
        writer.flush()?;

        queue_dispatcher.await??;

        info!(
            call_id,
            %file_hash,
            ?byte_range,
            "Completed reconstruct_file_to_writer_segmented"
        );

        Ok(total_written)
    }

    // Segmented download such that the file reconstruction and fetch info is not queried in its entirety
    // at the beginning of the download, but queried in segments. Range downloads are executed with
    // a certain degree of parallelism, and so does writing out to storage. Ideal when the external
    // storage is fast at seeks, e.g. RAM or SSDs.
    #[instrument(skip_all, name = "RemoteClient::reconstruct_file_segmented_parallel", fields(file.hash = file_hash.hex()
    ))]
    async fn reconstruct_file_to_writer_segmented_parallel_write(
        &self,
        file_hash: &MerkleHash,
        byte_range: Option<FileRange>,
        writer: &OutputProvider,
        progress_updater: Option<Arc<SingleItemProgressUpdater>>,
    ) -> Result<u64> {
        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        info!(
            call_id,
            %file_hash,
            ?byte_range,
            "Starting reconstruct_file_to_writer_segmented_parallel_write"
        );

        // Use the unlimited queue, as queue size is inherently bounded by degree of concurrency.
        let (task_tx, mut task_rx) =
            mpsc::unbounded_channel::<DownloadQueueItem<FetchTermDownloadOnceAndWriteEverywhereUsed>>();
        let mut running_downloads = JoinSet::<Result<TermDownloadResult<u64>>>::new();

        // derive the actual range to reconstruct
        let file_reconstruct_range = byte_range.unwrap_or_else(FileRange::full);
        let base_write_negative_offset = file_reconstruct_range.start;

        // kick-start the download by enqueue the fetch info task.
        task_tx.send(DownloadQueueItem::Metadata(FetchInfo::new(
            *file_hash,
            file_reconstruct_range,
            self.endpoint.clone(),
            self.authenticated_http_client_with_retry.clone(),
        )))?;

        // Start the queue processing logic
        //
        // If the queue item is `DownloadQueueItem::Metadata`, it fetches the file reconstruction info
        // of the first segment, whose size is linear to `num_concurrent_range_gets`. Once fetched, term
        // download tasks are enqueued and spawned with the degree of concurrency equal to `num_concurrent_range_gets`.
        // After the above, a task that defines fetching the remainder of the file reconstruction info is enqueued,
        // which will execute after the first of the above term download tasks finishes.
        let term_download_client = self.http_client_with_retry.clone();
        let download_scheduler = DownloadSegmentLengthTuner::from_configurable_constants();

        let download_concurrency_limiter =
            XetRuntime::current().global_semaphore(*DOWNLOAD_CHUNK_RANGE_CONCURRENCY_LIMITER);

        let process_result = move |result: TermDownloadResult<u64>,
                                   total_written: &mut u64,
                                   download_scheduler: &DownloadSegmentLengthTuner|
              -> Result<u64> {
            let write_len = result.payload;
            *total_written += write_len;

            // Now inspect the download metrics and tune the download degree of concurrency
            download_scheduler.tune_on(result)?;
            Ok(write_len)
        };

        let mut total_written = 0;
        while let Some(item) = task_rx.recv().await {
            // first try to join some tasks
            while let Some(result) = running_downloads.try_join_next() {
                let write_len = process_result(result??, &mut total_written, &download_scheduler)?;
                if let Some(updater) = progress_updater.as_ref() {
                    updater.update(write_len).await;
                }
            }

            match item {
                DownloadQueueItem::End => {
                    // everything processed
                    debug!(call_id, "download queue emptied");
                    break;
                },
                DownloadQueueItem::DownloadTask(term_download) => {
                    // acquire the permit before spawning the task, so that there's limited
                    // number of active downloads.
                    let permit = download_concurrency_limiter.clone().acquire_owned().await?;
                    debug!(call_id, "spawning 1 download task");
                    running_downloads.spawn(async move {
                        let data = term_download.run().await?;
                        drop(permit);
                        Ok(data)
                    });
                },
                DownloadQueueItem::Metadata(fetch_info) => {
                    // query for the file info of the first segment

                    let segment_size = download_scheduler.next_segment_size()?;
                    debug!(call_id, segment_size, "querying file info");
                    let (segment, maybe_remainder) = fetch_info.take_segment(segment_size);

                    let Some((offset_into_first_range, terms)) = segment.query().await? else {
                        // signal termination
                        task_tx.send(DownloadQueueItem::End)?;
                        continue;
                    };

                    let segment = Arc::new(segment);

                    // define the term download tasks
                    let tasks = map_fetch_info_into_download_tasks(
                        segment.clone(),
                        terms,
                        offset_into_first_range,
                        base_write_negative_offset,
                        self.chunk_cache.clone(),
                        term_download_client.clone(),
                        self.range_download_single_flight.clone(),
                        writer,
                    )
                    .await?;

                    debug!(call_id, num_tasks = tasks.len(), "enqueueing download tasks");
                    for task_def in tasks {
                        task_tx.send(DownloadQueueItem::DownloadTask(task_def))?;
                    }

                    // enqueue the remainder of file info fetch task
                    if let Some(remainder) = maybe_remainder {
                        task_tx.send(DownloadQueueItem::Metadata(remainder))?;
                    } else {
                        task_tx.send(DownloadQueueItem::End)?;
                    }
                },
            }
        }

        while let Some(result) = running_downloads.join_next().await {
            let write_len = process_result(result??, &mut total_written, &download_scheduler)?;
            if let Some(updater) = progress_updater.as_ref() {
                updater.update(write_len).await;
            }
        }

        info!(
            call_id,
            %file_hash,
            ?byte_range,
            "Completed reconstruct_file_to_writer_segmented_parallel_write"
        );

        Ok(total_written)
    }

    #[cfg(not(target_family = "wasm"))]
    pub async fn get_reconstruction(
        &self,
        file_id: &MerkleHash,
        bytes_range: Option<FileRange>,
    ) -> Result<Option<QueryReconstructionResponse>> {
        get_reconstruction_with_endpoint_and_client(
            &self.endpoint,
            &self.authenticated_http_client_with_retry,
            file_id,
            bytes_range,
        )
        .await
    }
}

#[cfg_attr(not(target_family = "wasm"), async_trait::async_trait)]
#[cfg_attr(target_family = "wasm", async_trait::async_trait(?Send))]
impl Client for RemoteClient {
    #[cfg(not(target_family = "wasm"))]
    #[instrument(skip_all, name = "RemoteClient::upload_xorb", fields(key = Key{prefix : prefix.to_string(), hash : serialized_cas_object.hash}.to_string(),
                 xorb.len = serialized_cas_object.serialized_data.len(), xorb.num_chunks = serialized_cas_object.num_chunks
    ))]
    async fn upload_xorb(
        &self,
        prefix: &str,
        serialized_cas_object: SerializedCasObject,
        upload_tracker: Option<Arc<CompletionTracker>>,
    ) -> Result<u64> {
        let key = Key {
            prefix: prefix.to_string(),
            hash: serialized_cas_object.hash,
        };

        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        let url = Url::parse(&format!("{}/xorbs/{key}", self.endpoint))?;

        let n_upload_bytes = serialized_cas_object.serialized_data.len() as u64;
        info!(
            call_id,
            prefix,
            hash=%serialized_cas_object.hash,
            size=n_upload_bytes,
            num_chunks=serialized_cas_object.num_chunks,
            "Starting upload_xorb API call",
        );

        // Backing out the incremental progress reporting for now until we figure out the middleware issue.
        use crate::upload_progress_stream::UploadProgressStream;

        let n_raw_bytes = serialized_cas_object.raw_num_bytes;
        let xorb_hash = serialized_cas_object.hash;

        let progress_callback = move |bytes_sent: u64| {
            if let Some(utr) = upload_tracker.as_ref() {
                // First, recalibrate the sending, as the compressed size is different from the actual data size.
                let adjusted_update = (bytes_sent * n_raw_bytes) / n_upload_bytes;

                utr.clone().register_xorb_upload_progress_background(xorb_hash, adjusted_update);
            }
        };

        let upload_stream = UploadProgressStream::new(
            serialized_cas_object.serialized_data,
            *UPLOAD_REPORTING_BLOCK_SIZE,
            progress_callback,
        );

        let xorb_uploaded = {
            if !self.dry_run {
                let client = self.authenticated_http_client.clone();

                let api_tag = "cas::upload_xorb";

                let response: UploadXorbResponse = RetryWrapper::new(api_tag)
                    .run_and_extract_json(move || {
                        let upload_stream = upload_stream.clone_with_reset();
                        let url = url.clone();

                        client
                            .post(url)
                            .with_extension(Api(api_tag))
                            .header(CONTENT_LENGTH, HeaderValue::from(n_upload_bytes)) // must be set because of streaming
                            .body(Body::wrap_stream(upload_stream))
                            .send()
                    })
                    .await?;

                response.was_inserted
            } else {
                true
            }
        };

        if !xorb_uploaded {
            info!(
                call_id,
                prefix,
                hash=%serialized_cas_object.hash,
                result="not_inserted",
                "Completed upload_xorb API call",
            );
        } else {
            info!(
                call_id,
                prefix,
                hash=%serialized_cas_object.hash,
                size=n_upload_bytes,
                result="inserted",
                "Completed upload_xorb API call",
            );
        }

        Ok(n_upload_bytes)
    }

    #[cfg(target_family = "wasm")]
    async fn upload_xorb(
        &self,
        prefix: &str,
        serialized_cas_object: SerializedCasObject,
        upload_tracker: Option<Arc<CompletionTracker>>,
    ) -> Result<u64> {
        let key = Key {
            prefix: prefix.to_string(),
            hash: serialized_cas_object.hash,
        };

        let url = Url::parse(&format!("{}/xorbs/{key}", self.endpoint))?;

        let n_upload_bytes = serialized_cas_object.serialized_data.len() as u64;

        let xorb_uploaded = self
            .authenticated_http_client
            .post(url)
            .with_extension(Api("cas::upload_xorb"))
            .body(serialized_cas_object.serialized_data)
            .send()
            .await?;

        Ok(n_upload_bytes)
    }

    fn use_xorb_footer(&self) -> bool {
        false
    }

    fn use_shard_footer(&self) -> bool {
        false
    }

    #[cfg(not(target_family = "wasm"))]
    async fn get_file(
        &self,
        hash: &MerkleHash,
        byte_range: Option<FileRange>,
        output_provider: &OutputProvider,
        progress_updater: Option<Arc<SingleItemProgressUpdater>>,
    ) -> Result<u64> {
        // If the user has set the `HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY=true` env variable, then we
        // should write the file to the output sequentially instead of in parallel.
        if *RECONSTRUCT_WRITE_SEQUENTIALLY {
            info!("reconstruct terms sequentially");
            self.reconstruct_file_to_writer_segmented(hash, byte_range, output_provider, progress_updater)
                .await
        } else {
            info!("reconstruct terms in parallel");
            self.reconstruct_file_to_writer_segmented_parallel_write(
                hash,
                byte_range,
                output_provider,
                progress_updater,
            )
            .await
        }
    }

    #[instrument(skip_all, name = "RemoteClient::get_file_reconstruction", fields(file.hash = file_hash.hex()
    ))]
    async fn get_file_reconstruction_info(
        &self,
        file_hash: &MerkleHash,
    ) -> Result<Option<(MDBFileInfo, Option<MerkleHash>)>> {
        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        let url = Url::parse(&format!("{}/reconstructions/{}", self.endpoint, file_hash.hex()))?;
        info!(call_id, %file_hash, "Starting get_file_reconstruction_info API call");

        let api_tag = "cas::get_reconstruction_info";
        let client = self.authenticated_http_client.clone();

        let response: QueryReconstructionResponse = RetryWrapper::new(api_tag)
            .run_and_extract_json(move || client.get(url.clone()).with_extension(Api(api_tag)).send())
            .await?;

        let terms_count = response.terms.len();
        let result = Some((
            MDBFileInfo {
                metadata: FileDataSequenceHeader::new(*file_hash, terms_count, false, false),
                segments: response
                    .terms
                    .into_iter()
                    .map(|ce| {
                        FileDataSequenceEntry::new(ce.hash.into(), ce.unpacked_length, ce.range.start, ce.range.end)
                    })
                    .collect(),
                verification: vec![],
                metadata_ext: None,
            },
            None,
        ));

        info!(call_id, %file_hash, terms_count, "Completed get_file_reconstruction_info API call");

        Ok(result)
    }

    #[instrument(skip_all, name = "RemoteClient::upload_shard", fields(shard.len = shard_data.len()))]
    async fn upload_shard(&self, shard_data: Bytes) -> Result<bool> {
        if self.dry_run {
            return Ok(true);
        }

        let size = shard_data.len();
        let call_id = FN_CALL_ID.fetch_add(1, Ordering::Relaxed);
        info!(call_id, size, "Starting upload_shard API");

        let api_tag = "cas::upload_shard";
        let client = self.authenticated_http_client.clone();

        let url = Url::parse(&format!("{}/shards", self.endpoint))?;

        let response: UploadShardResponse = RetryWrapper::new(api_tag)
            .run_and_extract_json(move || {
                client
                    .post(url.clone())
                    .with_extension(Api(api_tag))
                    .body(shard_data.clone())
                    .send()
            })
            .await?;

        let result = match response.result {
            UploadShardResponseType::Exists => {
                info!(call_id, size, result = "exists", "Completed upload_shard API call");
                false
            },
            UploadShardResponseType::SyncPerformed => {
                info!(call_id, size, result = "sync_performed", "Completed upload_shard API call",);
                true
            },
        };

        Ok(result)
    }

    async fn query_for_global_dedup_shard(&self, prefix: &str, chunk_hash: &MerkleHash) -> Result<Option<Bytes>> {
        let Some(response) = self.query_dedup_api(prefix, chunk_hash).await? else {
            return Ok(None);
        };

        Ok(Some(response.bytes().await?))
    }
}

#[cfg(test)]
#[cfg(not(target_family = "wasm"))]
mod tests {
    use std::collections::HashMap;

    use anyhow::Result;
    use cas_object::CompressionScheme;
    use cas_object::test_utils::*;
    use cas_types::{CASReconstructionFetchInfo, CASReconstructionTerm, ChunkRange};
    use deduplication::constants::MAX_XORB_BYTES;
    use httpmock::Method::GET;
    use httpmock::MockServer;
    use tracing_test::traced_test;
    use xet_runtime::XetRuntime;

    use super::*;
    use crate::output_provider::BufferProvider;

    #[ignore = "requires a running CAS server"]
    #[traced_test]
    #[test]
    fn test_basic_put() {
        // Arrange
        let prefix = PREFIX_DEFAULT;
        let raw_xorb = build_raw_xorb(3, ChunkSize::Random(512, 10248));

        let threadpool = XetRuntime::new().unwrap();
        let client = RemoteClient::new(CAS_ENDPOINT, &None, &None, None, "", false);

        let cas_object = build_and_verify_cas_object(raw_xorb, Some(CompressionScheme::LZ4));

        // Act
        let result = threadpool
            .external_run_async_task(async move { client.upload_xorb(prefix, cas_object, None).await })
            .unwrap();

        // Assert
        assert!(result.is_ok());
    }

    #[derive(Clone)]
    struct TestCase {
        file_hash: MerkleHash,
        reconstruction_response: QueryReconstructionResponse,
        file_range: FileRange,
        expected_data: Vec<u8>,
        expect_error: bool,
    }

    const NUM_CHUNKS: u32 = 128;

    const CHUNK_SIZE: u32 = 64 * 1024;

    macro_rules! mock_no_match_range_header {
        ($range_to_compare:expr) => {
            |req| {
                let Some(h) = &req.headers else {
                    return false;
                };
                let Some((_range_header, range_value)) =
                    h.iter().find(|(k, _v)| k.eq_ignore_ascii_case(RANGE.as_str()))
                else {
                    return false;
                };

                let Ok(range) = HttpRange::try_from(range_value.trim_start_matches("bytes=")) else {
                    return false;
                };

                range != $range_to_compare
            }
        };
    }

    #[test]
    fn test_reconstruct_file_full_file() -> Result<()> {
        // Arrange server
        let server = MockServer::start();

        let xorb_hash: MerkleHash = MerkleHash::default();
        let (cas_object, chunks_serialized, raw_data, _raw_data_chunk_hash_and_boundaries) =
            build_cas_object(NUM_CHUNKS, ChunkSize::Fixed(CHUNK_SIZE), CompressionScheme::ByteGrouping4LZ4);

        // Workaround to make this variable const. Change this accordingly if
        // real value of the two static variables below change.
        const FIRST_SEGMENT_SIZE: u64 = 16 * 64 * 1024 * 1024;
        assert_eq!(FIRST_SEGMENT_SIZE, *NUM_RANGE_IN_SEGMENT_BASE as u64 * *MAX_XORB_BYTES as u64);

        // Test case: full file reconstruction
        const FIRST_SEGMENT_FILE_RANGE: FileRange = FileRange {
            start: 0,
            end: FIRST_SEGMENT_SIZE,
            _marker: std::marker::PhantomData,
        };

        let test_case = TestCase {
            file_hash: MerkleHash::from_hex(&format!("{:0>64}", "1"))?, // "0....1"
            reconstruction_response: QueryReconstructionResponse {
                offset_into_first_range: 0,
                terms: vec![CASReconstructionTerm {
                    hash: xorb_hash.into(),
                    range: ChunkRange::new(0, NUM_CHUNKS),
                    unpacked_length: raw_data.len() as u32,
                }],
                fetch_info: HashMap::from([(
                    xorb_hash.into(),
                    vec![CASReconstructionFetchInfo {
                        range: ChunkRange::new(0, NUM_CHUNKS),
                        url: server.url(format!("/get_xorb/{xorb_hash}/")),
                        url_range: {
                            let (start, end) = cas_object.get_byte_offset(0, NUM_CHUNKS)?;
                            HttpRange::from(FileRange::new(start as u64, end as u64))
                        },
                    }],
                )]),
            },
            file_range: FileRange::full(),
            expected_data: raw_data,
            expect_error: false,
        };

        // Arrange server mocks
        let _mock_fi_416 = server.mock(|when, then| {
            when.method(GET)
                .path(format!("/reconstructions/{}", test_case.file_hash))
                .matches(mock_no_match_range_header!(HttpRange::from(FIRST_SEGMENT_FILE_RANGE)));
            then.status(416);
        });
        let _mock_fi_200 = server.mock(|when, then| {
            let w = when.method(GET).path(format!("/reconstructions/{}", test_case.file_hash));
            w.header(RANGE.as_str(), HttpRange::from(FIRST_SEGMENT_FILE_RANGE).range_header());
            then.status(200).json_body_obj(&test_case.reconstruction_response);
        });
        for (k, v) in &test_case.reconstruction_response.fetch_info {
            for term in v {
                let data = FileRange::from(term.url_range);
                let data = chunks_serialized[data.start as usize..data.end as usize].to_vec();
                let _mock_data = server.mock(|when, then| {
                    when.method(GET)
                        .path(format!("/get_xorb/{k}/"))
                        .header(RANGE.as_str(), term.url_range.range_header());
                    then.status(200).body(&data);
                });
            }
        }

        test_reconstruct_file(test_case, &server.base_url())
    }

    #[test]
    fn test_reconstruct_file_skip_front_bytes() -> Result<()> {
        // Arrange server
        let server = MockServer::start();

        let xorb_hash: MerkleHash = MerkleHash::default();
        let (cas_object, chunks_serialized, raw_data, _raw_data_chunk_hash_and_boundaries) =
            build_cas_object(NUM_CHUNKS, ChunkSize::Fixed(CHUNK_SIZE), CompressionScheme::ByteGrouping4LZ4);

        // Workaround to make this variable const. Change this accordingly if
        // real value of the two static variables below change.
        const FIRST_SEGMENT_SIZE: u64 = 16 * 64 * 1024 * 1024;
        assert_eq!(FIRST_SEGMENT_SIZE, *NUM_RANGE_IN_SEGMENT_BASE as u64 * *MAX_XORB_BYTES as u64);

        // Test case: skip first 100 bytes
        const SKIP_BYTES: u64 = 100;
        const FIRST_SEGMENT_FILE_RANGE: FileRange = FileRange {
            start: SKIP_BYTES,
            end: SKIP_BYTES + FIRST_SEGMENT_SIZE,
            _marker: std::marker::PhantomData,
        };

        let test_case = TestCase {
            file_hash: MerkleHash::from_hex(&format!("{:0>64}", "1"))?, // "0....1"
            reconstruction_response: QueryReconstructionResponse {
                offset_into_first_range: SKIP_BYTES,
                terms: vec![CASReconstructionTerm {
                    hash: xorb_hash.into(),
                    range: ChunkRange::new(0, NUM_CHUNKS),
                    unpacked_length: raw_data.len() as u32,
                }],
                fetch_info: HashMap::from([(
                    xorb_hash.into(),
                    vec![CASReconstructionFetchInfo {
                        range: ChunkRange::new(0, NUM_CHUNKS),
                        url: server.url(format!("/get_xorb/{xorb_hash}/")),
                        url_range: {
                            let (start, end) = cas_object.get_byte_offset(0, NUM_CHUNKS)?;
                            HttpRange::from(FileRange::new(start as u64, end as u64))
                        },
                    }],
                )]),
            },
            file_range: FileRange::new(SKIP_BYTES, u64::MAX),
            expected_data: raw_data[SKIP_BYTES as usize..].to_vec(),
            expect_error: false,
        };

        // Arrange server mocks
        let _mock_fi_416 = server.mock(|when, then| {
            when.method(GET)
                .path(format!("/reconstructions/{}", test_case.file_hash))
                .matches(mock_no_match_range_header!(HttpRange::from(FIRST_SEGMENT_FILE_RANGE)));
            then.status(416);
        });
        let _mock_fi_200 = server.mock(|when, then| {
            let w = when.method(GET).path(format!("/reconstructions/{}", test_case.file_hash));
            w.header(RANGE.as_str(), HttpRange::from(FIRST_SEGMENT_FILE_RANGE).range_header());
            then.status(200).json_body_obj(&test_case.reconstruction_response);
        });
        for (k, v) in &test_case.reconstruction_response.fetch_info {
            for term in v {
                let data = FileRange::from(term.url_range);
                let data = chunks_serialized[data.start as usize..data.end as usize].to_vec();
                let _mock_data = server.mock(|when, then| {
                    when.method(GET)
                        .path(format!("/get_xorb/{k}/"))
                        .header(RANGE.as_str(), term.url_range.range_header());
                    then.status(200).body(&data);
                });
            }
        }

        test_reconstruct_file(test_case, &server.base_url())
    }

    #[test]
    fn test_reconstruct_file_skip_back_bytes() -> Result<()> {
        // Arrange server
        let server = MockServer::start();

        let xorb_hash: MerkleHash = MerkleHash::default();
        let (cas_object, chunks_serialized, raw_data, _raw_data_chunk_hash_and_boundaries) =
            build_cas_object(NUM_CHUNKS, ChunkSize::Fixed(CHUNK_SIZE), CompressionScheme::ByteGrouping4LZ4);

        // Test case: skip last 100 bytes
        const FILE_SIZE: u64 = NUM_CHUNKS as u64 * CHUNK_SIZE as u64;
        const SKIP_BYTES: u64 = 100;
        const FIRST_SEGMENT_FILE_RANGE: FileRange = FileRange {
            start: 0,
            end: FILE_SIZE - SKIP_BYTES,
            _marker: std::marker::PhantomData,
        };

        let test_case = TestCase {
            file_hash: MerkleHash::from_hex(&format!("{:0>64}", "1"))?, // "0....1"
            reconstruction_response: QueryReconstructionResponse {
                offset_into_first_range: 0,
                terms: vec![CASReconstructionTerm {
                    hash: xorb_hash.into(),
                    range: ChunkRange::new(0, NUM_CHUNKS),
                    unpacked_length: raw_data.len() as u32,
                }],
                fetch_info: HashMap::from([(
                    xorb_hash.into(),
                    vec![CASReconstructionFetchInfo {
                        range: ChunkRange::new(0, NUM_CHUNKS),
                        url: server.url(format!("/get_xorb/{xorb_hash}/")),
                        url_range: {
                            let (start, end) = cas_object.get_byte_offset(0, NUM_CHUNKS)?;
                            HttpRange::from(FileRange::new(start as u64, end as u64))
                        },
                    }],
                )]),
            },
            file_range: FileRange::new(0, FILE_SIZE - SKIP_BYTES),
            expected_data: raw_data[..(FILE_SIZE - SKIP_BYTES) as usize].to_vec(),
            expect_error: false,
        };

        // Arrange server mocks
        let _mock_fi_416 = server.mock(|when, then| {
            when.method(GET)
                .path(format!("/reconstructions/{}", test_case.file_hash))
                .matches(mock_no_match_range_header!(HttpRange::from(FIRST_SEGMENT_FILE_RANGE)));
            then.status(416);
        });
        let _mock_fi_200 = server.mock(|when, then| {
            let w = when.method(GET).path(format!("/reconstructions/{}", test_case.file_hash));
            w.header(RANGE.as_str(), HttpRange::from(FIRST_SEGMENT_FILE_RANGE).range_header());
            then.status(200).json_body_obj(&test_case.reconstruction_response);
        });
        for (k, v) in &test_case.reconstruction_response.fetch_info {
            for term in v {
                let data = FileRange::from(term.url_range);
                let data = chunks_serialized[data.start as usize..data.end as usize].to_vec();
                let _mock_data = server.mock(|when, then| {
                    when.method(GET)
                        .path(format!("/get_xorb/{k}/"))
                        .header(RANGE.as_str(), term.url_range.range_header());
                    then.status(200).body(&data);
                });
            }
        }

        test_reconstruct_file(test_case, &server.base_url())
    }

    #[test]
    fn test_reconstruct_file_two_terms() -> Result<()> {
        // Arrange server
        let server = MockServer::start();

        let xorb_hash_1: MerkleHash = MerkleHash::from_hex(&format!("{:0>64}", "1"))?; // "0....1"
        let xorb_hash_2: MerkleHash = MerkleHash::from_hex(&format!("{:0>64}", "2"))?; // "0....2"
        let (cas_object, chunks_serialized, raw_data, _raw_data_chunk_hash_and_boundaries) =
            build_cas_object(NUM_CHUNKS, ChunkSize::Fixed(CHUNK_SIZE), CompressionScheme::ByteGrouping4LZ4);

        // Test case: two terms and skip first and last 100 bytes
        const FILE_SIZE: u64 = (NUM_CHUNKS - 1) as u64 * CHUNK_SIZE as u64;
        const SKIP_BYTES: u64 = 100;
        const FIRST_SEGMENT_FILE_RANGE: FileRange = FileRange {
            start: SKIP_BYTES,
            end: FILE_SIZE - SKIP_BYTES,
            _marker: std::marker::PhantomData,
        };

        let test_case = TestCase {
            file_hash: MerkleHash::from_hex(&format!("{:0>64}", "1"))?, // "0....3"
            reconstruction_response: QueryReconstructionResponse {
                offset_into_first_range: SKIP_BYTES,
                terms: vec![
                    CASReconstructionTerm {
                        hash: xorb_hash_1.into(),
                        range: ChunkRange::new(0, 5),
                        unpacked_length: CHUNK_SIZE * 5,
                    },
                    CASReconstructionTerm {
                        hash: xorb_hash_2.into(),
                        range: ChunkRange::new(6, NUM_CHUNKS),
                        unpacked_length: CHUNK_SIZE * (NUM_CHUNKS - 6),
                    },
                ],
                fetch_info: HashMap::from([
                    (
                        // this constructs the first term
                        xorb_hash_1.into(),
                        vec![CASReconstructionFetchInfo {
                            range: ChunkRange::new(0, 7),
                            url: server.url(format!("/get_xorb/{xorb_hash_1}/")),
                            url_range: {
                                let (start, end) = cas_object.get_byte_offset(0, 7)?;
                                HttpRange::from(FileRange::new(start as u64, end as u64))
                            },
                        }],
                    ),
                    (
                        // this constructs the second term
                        xorb_hash_2.into(),
                        vec![CASReconstructionFetchInfo {
                            range: ChunkRange::new(4, NUM_CHUNKS),
                            url: server.url(format!("/get_xorb/{xorb_hash_2}/")),
                            url_range: {
                                let (start, end) = cas_object.get_byte_offset(4, NUM_CHUNKS)?;
                                HttpRange::from(FileRange::new(start as u64, end as u64))
                            },
                        }],
                    ),
                ]),
            },
            file_range: FileRange::new(SKIP_BYTES, FILE_SIZE - SKIP_BYTES),
            expected_data: [
                &raw_data[SKIP_BYTES as usize..(5 * CHUNK_SIZE) as usize],
                &raw_data[(6 * CHUNK_SIZE) as usize..(NUM_CHUNKS * CHUNK_SIZE) as usize - SKIP_BYTES as usize],
            ]
            .concat(),
            expect_error: false,
        };

        // Arrange server mocks
        let _mock_fi_416 = server.mock(|when, then| {
            when.method(GET)
                .path(format!("/reconstructions/{}", test_case.file_hash))
                .matches(mock_no_match_range_header!(HttpRange::from(FIRST_SEGMENT_FILE_RANGE)));
            then.status(416);
        });
        let _mock_fi_200 = server.mock(|when, then| {
            let w = when.method(GET).path(format!("/reconstructions/{}", test_case.file_hash));
            w.header(RANGE.as_str(), HttpRange::from(FIRST_SEGMENT_FILE_RANGE).range_header());
            then.status(200).json_body_obj(&test_case.reconstruction_response);
        });
        for (k, v) in &test_case.reconstruction_response.fetch_info {
            for term in v {
                let data = FileRange::from(term.url_range);
                let data = chunks_serialized[data.start as usize..data.end as usize].to_vec();
                let _mock_data = server.mock(|when, then| {
                    when.method(GET)
                        .path(format!("/get_xorb/{k}/"))
                        .header(RANGE.as_str(), term.url_range.range_header());
                    then.status(200).body(&data);
                });
            }
        }

        test_reconstruct_file(test_case, &server.base_url())
    }

    fn test_reconstruct_file(test_case: TestCase, endpoint: &str) -> Result<()> {
        let threadpool = XetRuntime::new()?;

        // test reconstruct and sequential write
        let test = test_case.clone();
        let client = RemoteClient::new(endpoint, &None, &None, None, "", false);
        let provider = BufferProvider::default();
        let buf = provider.buf.clone();
        let writer = OutputProvider::Buffer(provider);
        let resp = threadpool.external_run_async_task(async move {
            client
                .reconstruct_file_to_writer_segmented(&test.file_hash, Some(test.file_range), &writer, None)
                .await
        })?;

        assert_eq!(test.expect_error, resp.is_err(), "{:?}", resp.err());
        if !test.expect_error {
            assert_eq!(test.expected_data.len() as u64, resp.unwrap());
            assert_eq!(test.expected_data, buf.value());
        }

        // test reconstruct and parallel write
        let test = test_case;
        let client = RemoteClient::new(endpoint, &None, &None, None, "", false);
        let provider = BufferProvider::default();
        let buf = provider.buf.clone();
        let writer = OutputProvider::Buffer(provider);
        let resp = threadpool.external_run_async_task(async move {
            client
                .reconstruct_file_to_writer_segmented_parallel_write(
                    &test.file_hash,
                    Some(test.file_range),
                    &writer,
                    None,
                )
                .await
        })?;

        assert_eq!(test.expect_error, resp.is_err());
        if !test.expect_error {
            assert_eq!(test.expected_data.len() as u64, resp.unwrap());
            let value = buf.value();
            assert_eq!(&test.expected_data[..100], &value[..100]);
            let idx = test.expected_data.len() - 100;
            assert_eq!(&test.expected_data[idx..], &value[idx..]);
            assert_eq!(test.expected_data, value);
        }

        Ok(())
    }
}
