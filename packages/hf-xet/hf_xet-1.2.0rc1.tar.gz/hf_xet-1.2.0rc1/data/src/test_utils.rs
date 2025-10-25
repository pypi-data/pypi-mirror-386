use std::fs::{File, create_dir_all, read_dir};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::sync::Arc;

use cas_client::{FileProvider, OutputProvider};
use progress_tracking::TrackingProgressUpdater;
use rand::prelude::*;
use tempfile::TempDir;

use crate::configurations::TranslatorConfig;
use crate::data_client::clean_file;
use crate::{FileDownloader, FileUploadSession, XetFileInfo};

/// Creates or overwrites a single file in `dir` with `size` bytes of random data.
/// Panics on any I/O error. Returns the total number of bytes written (=`size`).
pub fn create_random_file(path: impl AsRef<Path>, size: usize, seed: u64) -> usize {
    let path = path.as_ref();

    let dir = path.parent().unwrap();

    // Make sure the directory exists, or create it.
    create_dir_all(dir).unwrap();

    let mut rng = StdRng::seed_from_u64(seed);

    // Build the path to the file, create the file, and write random data.
    let mut file = File::create(path).unwrap();

    let mut buffer = vec![0_u8; size];
    rng.fill_bytes(&mut buffer);

    file.write_all(&buffer).unwrap();

    size
}

/// Creates a collection of random files, each with a deterministic seed.  
/// the total number of bytes written for all files combined.
pub fn create_random_files(dir: impl AsRef<Path>, files: &[(impl AsRef<str>, usize)], seed: u64) -> usize {
    let dir = dir.as_ref();

    let mut total_bytes = 0;
    let mut rng = SmallRng::seed_from_u64(seed);

    for (file_name, size) in files {
        total_bytes += create_random_file(dir.join(file_name.as_ref()), *size, rng.random());
    }
    total_bytes
}

/// Creates or overwrites a single file in `dir` with consecutive segments determined by the list of [(size, seed)].
/// Panics on any I/O error. Returns the total number of bytes written (=`size`).
pub fn create_random_multipart_file(path: impl AsRef<Path>, segments: &[(usize, u64)]) -> usize {
    let path = path.as_ref();
    let dir = path.parent().unwrap();

    // Make sure the directory exists, or create it.
    create_dir_all(dir).unwrap();

    // Build the path to the file, create the file, and write random data.
    let mut file = File::create(path).unwrap();

    let mut total_size = 0;
    for &(size, seed) in segments {
        let mut rng = StdRng::seed_from_u64(seed);

        let mut buffer = vec![0_u8; size];
        rng.fill_bytes(&mut buffer);
        file.write_all(&buffer).unwrap();
        total_size += size;
    }
    total_size
}

/// Panics if `dir1` and `dir2` differ in terms of files or file contents.
/// Uses `unwrap()` everywhere; intended for test-only use.
pub fn verify_directories_match(dir1: impl AsRef<Path>, dir2: impl AsRef<Path>) {
    let dir1 = dir1.as_ref();
    let dir2 = dir2.as_ref();

    let mut files_in_dir1 = Vec::new();
    for entry in read_dir(dir1).unwrap() {
        let entry = entry.unwrap();
        assert!(entry.file_type().unwrap().is_file());
        files_in_dir1.push(entry.file_name());
    }

    let mut files_in_dir2 = Vec::new();
    for entry in read_dir(dir2).unwrap() {
        let entry = entry.unwrap();
        assert!(entry.file_type().unwrap().is_file());
        files_in_dir2.push(entry.file_name());
    }

    files_in_dir1.sort();
    files_in_dir2.sort();

    if files_in_dir1 != files_in_dir2 {
        panic!(
            "Directories differ: file sets are not the same.\n \
             dir1: {files_in_dir1:?}\n dir2: {files_in_dir2:?}"
        );
    }

    // Compare file contents byte-for-byte
    for file_name in &files_in_dir1 {
        let path1 = dir1.join(file_name);
        let path2 = dir2.join(file_name);

        let mut buf1 = Vec::new();
        let mut buf2 = Vec::new();

        File::open(&path1).unwrap().read_to_end(&mut buf1).unwrap();
        File::open(&path2).unwrap().read_to_end(&mut buf2).unwrap();

        if buf1 != buf2 {
            panic!(
                "File contents differ for {file_name:?}\n \
                 dir1 path: {path1:?}\n dir2 path: {path2:?}"
            );
        }
    }
}

pub struct LocalHydrateDehydrateTest {
    _temp_dir: TempDir,
    pub cas_dir: PathBuf,
    pub src_dir: PathBuf,
    pub ptr_dir: PathBuf,
    pub dest_dir: PathBuf,
}

impl Default for LocalHydrateDehydrateTest {
    fn default() -> Self {
        let _temp_dir = TempDir::new().unwrap();
        let temp_path = _temp_dir.path();

        let s = Self {
            cas_dir: temp_path.join("cas"),
            src_dir: temp_path.join("src"),
            ptr_dir: temp_path.join("pointers"),
            dest_dir: temp_path.join("dest"),
            _temp_dir,
        };
        std::fs::create_dir_all(&s.cas_dir).unwrap();
        std::fs::create_dir_all(&s.src_dir).unwrap();
        std::fs::create_dir_all(&s.ptr_dir).unwrap();
        std::fs::create_dir_all(&s.dest_dir).unwrap();

        s
    }
}

impl LocalHydrateDehydrateTest {
    pub async fn new_upload_session(
        &self,
        progress_tracker: Option<Arc<dyn TrackingProgressUpdater>>,
    ) -> Arc<FileUploadSession> {
        let config = TranslatorConfig::local_config(&self.cas_dir).unwrap();
        FileUploadSession::new(config.clone(), progress_tracker).await.unwrap()
    }

    pub async fn clean_all_files(&self, upload_session: &Arc<FileUploadSession>, sequential: bool) {
        create_dir_all(&self.ptr_dir).unwrap();

        if sequential {
            for entry in read_dir(&self.src_dir).unwrap() {
                let entry = entry.unwrap();
                let out_file = self.ptr_dir.join(entry.file_name());
                let upload_session = upload_session.clone();

                if sequential {
                    let (pf, metrics) = clean_file(upload_session.clone(), entry.path()).await.unwrap();
                    assert_eq!({ metrics.total_bytes }, entry.metadata().unwrap().len());
                    std::fs::write(out_file, pf.as_pointer_file().unwrap().as_bytes()).unwrap();

                    // Force a checkpoint after every file.
                    upload_session.checkpoint().await.unwrap();
                }
            }
        } else {
            let files: Vec<PathBuf> = read_dir(&self.src_dir)
                .unwrap()
                .map(|entry| self.src_dir.join(entry.unwrap().file_name()))
                .collect();

            let clean_results = upload_session.upload_files(&files).await.unwrap();

            for (i, xf) in clean_results.into_iter().enumerate() {
                std::fs::write(self.ptr_dir.join(files[i].file_name().unwrap()), serde_json::to_string(&xf).unwrap())
                    .unwrap();
            }
        }
    }

    pub async fn dehydrate(&self, sequential: bool) {
        let upload_session = self.new_upload_session(None).await;
        self.clean_all_files(&upload_session, sequential).await;

        upload_session.finalize().await.unwrap();
    }

    pub async fn hydrate(&self) {
        let config = TranslatorConfig::local_config(&self.cas_dir).unwrap();

        create_dir_all(&self.dest_dir).unwrap();

        let downloader = FileDownloader::new(config).await.unwrap();

        for entry in read_dir(&self.ptr_dir).unwrap() {
            let entry = entry.unwrap();

            let out_filename = self.dest_dir.join(entry.file_name());

            // Create an output file for writing
            let file_out = OutputProvider::File(FileProvider::new(out_filename.clone()));

            // Pointer file.
            let xf: XetFileInfo = serde_json::from_reader(File::open(entry.path()).unwrap()).unwrap();

            downloader
                .smudge_file_from_hash(
                    &xf.merkle_hash().unwrap(),
                    out_filename.to_string_lossy().into(),
                    &file_out,
                    None,
                    None,
                )
                .await
                .unwrap();
        }
    }

    pub fn verify_src_dest_match(&self) {
        verify_directories_match(&self.src_dir, &self.dest_dir);
    }
}
