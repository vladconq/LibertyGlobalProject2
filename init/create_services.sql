CREATE TABLE services
(
  id SERIAL PRIMARY KEY,
  ip character varying NOT NULL,
  port integer NOT NULL,
  available boolean NOT NULL
);

INSERT INTO services (ip, port, available) VALUES
('127.0.0.1', '44444', True),
('127.0.0.1', '55555', False),
('127.0.0.1', '33333', True),
('127.0.0.1', '22222', True),
('127.0.0.1', '11111', True),
('127.16.0.15', '22222', False),
('127.16.0.15', '33333', False),
('172.217.21.142', '80', True);
