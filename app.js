const express = require('express');
const { Pool } = require('pg');
const axios = require('axios');
require('dotenv').config();

const app = express();
app.use(express.json());

// Conexão com Postgres (URL do Render)
const pool = new Pool({ connectionString: process.env.DATABASE_URL });

// Rota para puxar dados do CPF
app.post('/dados-cpf', async (req, res) => {
  const { cpf } = req.body;

  // Validação básica
  if (!cpf || cpf.replace(/[^\d]/g, '').length !== 11) {
    return res.status(400).json({ erro: 'CPF inválido' });
  }

  try {
    // 1. Checa cache
    const cache = await pool.query('SELECT dados FROM cpfs WHERE cpf = $1', [cpf]);
    if (cache.rows.length > 0) {
      return res.json({ ...cache.rows[0].dados, fonte: 'cache' });
    }

    // 2. Consulta API SintegraWS
    const token = process.env.SINTEGRA_TOKEN;
    const response = await axios.get(
      `https://www.sintegraws.com.br/api/v1/execute-api.php?token=${token}&cpf=${cpf}&plugin=RF`
    );

    if (response.data.status !== 'OK') {
      return res.status(404).json({ erro: 'Dados não encontrados' });
    }

    const dados = response.data;

    // 3. Salva no cache
    await pool.query(
      'INSERT INTO cpfs (cpf, dados) VALUES ($1, $2) ON CONFLICT (cpf) DO UPDATE SET dados = $2',
      [cpf, dados]
    );

    res.json({ ...dados, fonte: 'api' });
  } catch (error) {
    res.status(500).json({ erro: 'Erro interno' });
  }
});

// Cria tabela no Postgres (rode 1x no console do Render)
pool.query(`
  CREATE TABLE IF NOT EXISTS cpfs (
    cpf VARCHAR(11) PRIMARY KEY,
    dados JSONB NOT NULL
  );
`);

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`API rodando na porta ${PORT}`));