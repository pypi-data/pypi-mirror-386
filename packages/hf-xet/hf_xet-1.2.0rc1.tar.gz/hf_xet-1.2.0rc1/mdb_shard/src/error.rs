use std::io;

use merklehash::MerkleHash;
use thiserror::Error;
use utils::RwTaskLockError;

#[non_exhaustive]
#[derive(Error, Debug)]
pub enum MDBShardError {
    #[error("File I/O error")]
    IOError(#[from] io::Error),

    #[error("Too many collisions when searching for truncated hash : {0}")]
    TruncatedHashCollisionError(u64),

    #[error("Shard version error: {0}")]
    ShardVersionError(String),

    #[error("Bad file name format: {0}")]
    BadFilename(String),

    #[error("Other Internal Error: {0}")]
    InternalError(anyhow::Error),

    #[error("Shard not found")]
    ShardNotFound(MerkleHash),

    #[error("File not found")]
    FileNotFound(MerkleHash),

    #[error("Query failed: {0}")]
    QueryFailed(String),

    #[error("Smudge query policy Error: {0}")]
    SmudgeQueryPolicyError(String),

    #[error("Runtime Error (task scheduler): {0}")]
    TaskRuntimeError(#[from] RwTaskLockError),

    #[error("Runtime Error (task scheduler): {0}")]
    TaskJoinError(#[from] tokio::task::JoinError),

    #[error("InvalidShard {0}")]
    InvalidShard(String),

    #[error("Error: {0}")]
    Other(String),
}

// Define our own result type here (this seems to be the standard).
pub type Result<T> = std::result::Result<T, MDBShardError>;

// For error checking
impl PartialEq for MDBShardError {
    fn eq(&self, other: &MDBShardError) -> bool {
        match (self, other) {
            (MDBShardError::IOError(e1), MDBShardError::IOError(e2)) => e1.kind() == e2.kind(),
            _ => false,
        }
    }
}

impl MDBShardError {
    pub fn other(inner: impl ToString) -> Self {
        Self::Other(inner.to_string())
    }

    pub fn invalid_shard(inner: impl ToString) -> Self {
        Self::InvalidShard(inner.to_string())
    }
}
