CREATE TABLE IF NOT EXISTS vehicles 
(
    "unique_id" TEXT NOT NULL,
    "veh_type" TEXT NOT NULL,
    "traveled_distance" FLOAT DEFAULT NULL,
    "avg_speed" FLOAT DEFAULT NULL,
    "track_id" INT DEFAULT NULL,
    PRIMARY KEY ("unique_id")
);