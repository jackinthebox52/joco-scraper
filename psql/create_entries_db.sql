CREATE TABLE IF NOT EXISTS ENTRIES(
        ID          VARCHAR (50) PRIMARY KEY NOT NULL,
        LINK INT   NOT NULL,
        OFFENSE          VARCHAR (100) NOT NULL,
        FNAME           VARCHAR (50)    NOT NULL,
        LNAME           VARCHAR (50)    NOT NULL,
        BOOKED           TIMESTAMP    NOT NULL,
        RELEASED           TIMESTAMP,
        BOND           REAL    NOT NULL,
        HOUSED           VARCHAR (50)    NOT NULL,
        AGE            INT     NOT NULL,
        CHARGE_TYPE        VARCHAR (50)
);


GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO *user*;

GRANT ALL PRIVILEGES ON DATABASE roster TO *user*;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO *user*;
