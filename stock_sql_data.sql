create database stock_market_db;
create table stock_data;
CREATE TABLE IF NOT EXISTS stock_data1 (
    id SERIAL PRIMARY KEY,
    Ticker VARCHAR(20),
    date DATE,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT
);
SELECT * FROM stock_data1;