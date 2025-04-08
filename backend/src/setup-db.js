const { pool } = require('./db');
const fs = require('fs');
const path = require('path');

async function setupDatabase() {
  const client = await pool.connect();
  
  try {
    // Read and execute schema.sql
    const schemaPath = path.join(__dirname, 'schema.sql');
    const schemaSQL = fs.readFileSync(schemaPath, 'utf8');
    
    console.log('Creating schema and tables...');
    await client.query(schemaSQL);
    console.log('Database setup completed successfully!');
  } catch (err) {
    console.error('Error setting up database:', err);
  } finally {
    client.release();
  }
}

setupDatabase();