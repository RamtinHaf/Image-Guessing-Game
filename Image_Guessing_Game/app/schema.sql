-- ---
-- Globals
-- ---

-- SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
-- SET FOREIGN_KEY_CHECKS=0;

-- ---
-- Table 'Users'
-- 
-- ---

DROP TABLE IF EXISTS [Users];

CREATE TABLE [Users] (
  id INTEGER PRIMARY KEY,
  username VARCHAR,
  [password] VARCHAR,
  points INTEGER default 0
);

-- ---
-- Table 'Games'
-- 
-- ---

DROP TABLE IF EXISTS [Games];

CREATE TABLE [Games] (
  id VARCHAR,
  guessers VARCHAR,
  proposer VARCHAR,
  imagepath VARCHAR,
  label VARCHAR,
  proposedimages VARCHAR,
  points INTEGER,
  successrate REAL,
  gamemode INTEGER
);
