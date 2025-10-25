use std::time::Duration;

use utils::ByteSize;

utils::configurable_constants! {

    /// The target shard size; shards.
    ref MDB_SHARD_TARGET_SIZE: u64 = 64 * 1024 * 1024;

    /// Maximum shard size; small shards are aggregated until they are at most this.
    ref MDB_SHARD_MAX_TARGET_SIZE: u64 = 64 * 1024 * 1024;

    /// The global dedup chunk modulus; a chunk is considered global dedup
    /// eligible if the hash modulus this value is zero.
    ref MDB_SHARD_GLOBAL_DEDUP_CHUNK_MODULUS: u64 = release_fixed(1024);

    /// The (soft) maximum size in bytes of the shard cache.  Default is 16 GB.
    ///
    /// As a rough calculation, a cache of size X will allow for dedup against data
    /// of size 1000 * X.  The default would allow a 16 TB repo to be deduped effectively.
    ///
    /// Note the cache is pruned to below this value at the beginning of a session,
    /// but during a single session new shards may be added such that this limit is exceeded.
    ref SHARD_CACHE_SIZE_LIMIT : ByteSize = ByteSize::from("16gb");

    /// The amount of time a shard should be expired by before it's deleted, in seconds.
    /// By default set to 7 days.
    ref MDB_SHARD_EXPIRATION_BUFFER: Duration = Duration::from_secs(7 * 24 * 3600);

    /// The maximum size of the chunk index table that's stored in memory.  After this,
    /// no new chunks are loaded for deduplication.
    ref CHUNK_INDEX_TABLE_MAX_SIZE: usize = 64 * 1024 * 1024;
}

// How the MDB_SHARD_GLOBAL_DEDUP_CHUNK_MODULUS is used.
pub fn hash_is_global_dedup_eligible(h: &merklehash::MerkleHash) -> bool {
    (*h) % *MDB_SHARD_GLOBAL_DEDUP_CHUNK_MODULUS == 0
}
