-- migrate:up

create TYPE protocol as ENUM ('http', 'https');

create table check_results (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    regex TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    response_time_ms INTEGER NOT NULL,
    response_code SMALLINT NOT NULL,
    regex_match BOOLEAN
);

-- migrate:down
drop table check_results;
