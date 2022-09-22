CREATE TABLE IF NOT EXISTS trajectories
(
    "id" SERIAL NOT NULL,
    "unique_id" TEXT NOT NULL,
    "lat" FLOAT NOT NULL,
    "lon" FLOAT DEFAULT NULL,
    "speed" FLOAT DEFAULT NULL,
    "lon_acc" FLOAT DEFAULT NULL,
    "lat_acc" FLOAT DEFAULT NULL,
    "time" FLOAT DEFAULT NULL,
    PRIMARY KEY ("id"),
    CONSTRAINT fk_vehicles
        FOREIGN KEY("unique_id") 
            REFERENCES vehicles(unique_id)
            ON DELETE CASCADE
    
);
