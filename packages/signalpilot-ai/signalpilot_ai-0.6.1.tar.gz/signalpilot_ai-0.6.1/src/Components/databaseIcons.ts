import { LabIcon } from '@jupyterlab/ui-components';
import postgresqlIcon from '../../style/icons/databases/postgresql.svg';
import mysqlIcon from '../../style/icons/databases/mysql.svg';
import snowflakeIcon from '../../style/icons/databases/snowflake.svg';
import connectionIcon from '../../style/icons/databases/connection.svg';

export const POSTGRESQL_ICON = new LabIcon({
  name: 'signalpilot-ai:postgresql-icon',
  svgstr: postgresqlIcon
});

export const MYSQL_ICON = new LabIcon({
  name: 'signalpilot-ai:mysql-icon',
  svgstr: mysqlIcon
});

export const SNOWFLAKE_ICON = new LabIcon({
  name: 'signalpilot-ai:snowflake-icon',
  svgstr: snowflakeIcon
});

export const CONNECTION_ICON = new LabIcon({
  name: 'signalpilot-ai:connection-icon',
  svgstr: connectionIcon
});
