-- Based on the NEA data dictionary. Lines marked (ADDED) are gaps I spotted.
DROP TABLE IF EXISTS route_tracking;
DROP TABLE IF EXISTS lesson_route;
DROP TABLE IF EXISTS lesson_feedback;
DROP TABLE IF EXISTS booking_slot;
DROP TABLE IF EXISTS held_slot;
DROP TABLE IF EXISTS temporary_hold;
DROP TABLE IF EXISTS lesson_booking;
DROP TABLE IF EXISTS availability_slot;
DROP TABLE IF EXISTS timetable;
DROP TABLE IF EXISTS progress_tracker;
DROP TABLE IF EXISTS notification;
DROP TABLE IF EXISTS student;
DROP TABLE IF EXISTS instructor;
DROP TABLE IF EXISTS account;
 
CREATE TABLE account (
    account_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    account_type  TEXT NOT NULL CHECK (account_type IN ('STUDENT','INSTRUCTOR')),
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL
);
 
CREATE TABLE instructor (
    instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id    INTEGER NOT NULL UNIQUE REFERENCES account(account_id),
    linking_code  TEXT NULL UNIQUE,
    adi_number    TEXT  -- (ADDED) SC15 needs ADI certification details
);
 
CREATE TABLE student (
    student_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id        INTEGER NOT NULL UNIQUE REFERENCES account(account_id),
    instructor_id     INTEGER REFERENCES instructor(instructor_id),
    transmission_type TEXT NOT NULL CHECK (transmission_type IN ('MANUAL','AUTOMATIC')),
    address           TEXT  -- (FIXED) was VARCHAR(10) in the data dictionary
);
 
CREATE TABLE timetable (
    timetable_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    instructor_id    INTEGER NOT NULL REFERENCES instructor(instructor_id),
    timetable_status TEXT NOT NULL CHECK (timetable_status IN ('DRAFT','PUBLISHED')),
    published_at     TEXT
);
 
CREATE TABLE availability_slot (
    slot_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    timetable_id INTEGER NOT NULL REFERENCES timetable(timetable_id),
    slot_date   TEXT NOT NULL,   -- 'YYYY-MM-DD'
    start_time  TEXT NOT NULL,   -- 'HH:MM'
    end_time    TEXT NOT NULL,
    slot_status TEXT NOT NULL DEFAULT 'AVAILABLE'
                CHECK (slot_status IN ('AVAILABLE','HELD','BOOKED')),
    CHECK (end_time > start_time)
);
 
CREATE TABLE temporary_hold (
    hold_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES student(student_id),
    created_at  TEXT NOT NULL,
    expires_at  TEXT NOT NULL,
    hold_status TEXT NOT NULL DEFAULT 'ACTIVE'
                CHECK (hold_status IN ('ACTIVE','EXPIRED','RELEASED'))
);
 
CREATE TABLE held_slot (
    hold_id INTEGER NOT NULL REFERENCES temporary_hold(hold_id),
    slot_id INTEGER NOT NULL REFERENCES availability_slot(slot_id),
    PRIMARY KEY (hold_id, slot_id)
);
 
CREATE TABLE lesson_booking (
    lesson_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id          INTEGER NOT NULL REFERENCES student(student_id),
    instructor_id       INTEGER NOT NULL REFERENCES instructor(instructor_id),
    lesson_date         TEXT NOT NULL,
    start_time          TEXT NOT NULL,
    end_time            TEXT NOT NULL,
    duration_minutes    INTEGER NOT NULL CHECK (duration_minutes > 0),
    booking_status      TEXT NOT NULL DEFAULT 'CONFIRMED'
                        CHECK (booking_status IN ('CONFIRMED','CANCELLED')),
    lesson_status       TEXT NOT NULL DEFAULT 'SCHEDULED'
                        CHECK (lesson_status IN ('SCHEDULED','IN_PROGRESS','COMPLETED')),
    lesson_start_time   TEXT,
    lesson_end_time     TEXT,
    gps_tracking_status TEXT CHECK (gps_tracking_status IN ('ACTIVE','STOPPED')),
    recurring           INTEGER NOT NULL DEFAULT 0  -- (ADDED) SC6 weekly repeat flag
);
 
CREATE TABLE booking_slot (
    lesson_id INTEGER NOT NULL REFERENCES lesson_booking(lesson_id),
    slot_id   INTEGER NOT NULL REFERENCES availability_slot(slot_id),
    PRIMARY KEY (lesson_id, slot_id)
);
 
CREATE TABLE lesson_feedback (
    feedback_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id                  INTEGER NOT NULL UNIQUE REFERENCES lesson_booking(lesson_id),
    student_feedback           TEXT,  -- private: never SELECT this in instructor queries (SC10)
    instructor_feedback        TEXT,
    instructor_feedback_status TEXT NOT NULL DEFAULT 'PENDING'
                               CHECK (instructor_feedback_status IN ('PENDING','SUBMITTED'))
);
 
CREATE TABLE lesson_route (
    route_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id        INTEGER NOT NULL UNIQUE REFERENCES lesson_booking(lesson_id),
    route_created_at TEXT NOT NULL
);
 
CREATE TABLE route_tracking (
    coordinate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_id      INTEGER NOT NULL REFERENCES lesson_route(route_id),
    latitude      REAL NOT NULL CHECK (latitude  BETWEEN -90  AND 90),
    longitude     REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    recorded_at   TEXT NOT NULL
);
 
CREATE TABLE progress_tracker (
    progress_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id            INTEGER NOT NULL UNIQUE REFERENCES student(student_id),
    theory_test_booked    INTEGER NOT NULL DEFAULT 0,
    theory_test_passed    INTEGER NOT NULL DEFAULT 0,
    practical_test_booked INTEGER NOT NULL DEFAULT 0,
    practical_test_passed INTEGER NOT NULL DEFAULT 0
);
 
-- (ADDED) Cancellation/reschedule notices and reminders need somewhere to live
CREATE TABLE notification (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id      INTEGER NOT NULL REFERENCES account(account_id),
    message         TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    is_read         INTEGER NOT NULL DEFAULT 0
);
 