SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: protocol; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.protocol AS ENUM (
    'http',
    'https'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: check_results; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.check_results (
    id integer NOT NULL,
    url text NOT NULL,
    regex text,
    start_time timestamp with time zone NOT NULL,
    response_time_ms integer NOT NULL,
    response_code smallint NOT NULL,
    regex_match boolean
);


--
-- Name: check_results_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.check_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: check_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.check_results_id_seq OWNED BY public.check_results.id;


--
-- Name: schema_migrations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_migrations (
    version character varying(255) NOT NULL
);


--
-- Name: check_results id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.check_results ALTER COLUMN id SET DEFAULT nextval('public.check_results_id_seq'::regclass);


--
-- Name: check_results check_results_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.check_results
    ADD CONSTRAINT check_results_pkey PRIMARY KEY (id);


--
-- Name: schema_migrations schema_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_migrations
    ADD CONSTRAINT schema_migrations_pkey PRIMARY KEY (version);


--
-- PostgreSQL database dump complete
--


--
-- Dbmate schema migrations
--

INSERT INTO public.schema_migrations (version) VALUES
    ('20200705193405');
