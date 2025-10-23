#include <dftracer/utils/indexer/sqlite/statement.h>
#include <dftracer/utils/indexer/tar/queries/queries.h>

namespace dftracer::utils::tar_indexer {

void insert_file_record(const SqliteDatabase &db,
                        const std::string &tar_gz_path_logical_path,
                        std::size_t bytes, std::time_t file_mtime,
                        std::uint64_t file_hash, int &db_file_id) {
    SqliteStmt stmt(db,
                    "INSERT INTO files(logical_name, byte_size, "
                    "mtime_unix, hash) "
                    "VALUES(?, ?, ?, ?) "
                    "ON CONFLICT(logical_name) DO UPDATE SET "
                    "byte_size=excluded.byte_size, "
                    "mtime_unix=excluded.mtime_unix, "
                    "hash=excluded.hash "
                    "RETURNING id;");

    stmt.bind_text(1, tar_gz_path_logical_path);
    stmt.bind_int64(2, static_cast<int64_t>(bytes));
    stmt.bind_int64(3, static_cast<int64_t>(file_mtime));
    stmt.bind_int64(4, static_cast<int64_t>(file_hash));

    int rc = sqlite3_step(stmt);
    if (rc != SQLITE_ROW && rc != SQLITE_DONE) {
        throw IndexerError(
            IndexerError::Type::DATABASE_ERROR,
            "Insert failed: " + std::string(sqlite3_errmsg(db.get())));
    }

    db_file_id = sqlite3_column_int(stmt, 0);
}

}  // namespace dftracer::utils::tar_indexer
