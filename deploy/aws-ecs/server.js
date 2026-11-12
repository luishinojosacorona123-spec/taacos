const http = require('http');
const os = require('os');

const port = process.env.PORT || 8080;
const alumno = process.env.ALUMNO || 'Luis Antonio Hinojosa Corona';
const version = process.env.VERSION || 'v1';

const server = http.createServer((req, res) => {
  // 1. Endpoint de salud para el Target Group del Load Balancer
  if (req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'RentMetrics', version: version }));
    return;
  }

  // 2. Pagina principal servida a los usuarios
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(`<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RentMetrics · AWS ECS Fargate</title>
  <style>
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      background: #f1f5f9;
      color: #0f172a;
      padding: 1.5rem;
    }
    .card {
      background: #ffffff;
      padding: 2.5rem;
      border-radius: 12px;
      box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
      max-width: 540px;
      width: 100%;
      border-top: 6px solid #1e3a8a;
    }
    .badge {
      display: inline-block;
      background: #dbeafe;
      color: #1e40af;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 1.25rem;
    }
    h1 {
      margin: 0 0 0.5rem 0;
      color: #0f172a;
      font-size: 1.75rem;
      letter-spacing: -0.025em;
    }
    p.lead {
      margin: 0 0 1.5rem 0;
      color: #475569;
      font-size: 1rem;
    }
    .info-list {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 1rem 1.25rem;
      margin-bottom: 1.5rem;
    }
    .info-item {
      display: flex;
      justify-content: space-between;
      padding: 0.4rem 0;
      border-bottom: 1px solid #f1f5f9;
      font-size: 0.925rem;
    }
    .info-item:last-child { border-bottom: none; }
    .info-item span.label { color: #64748b; font-weight: 500; }
    .info-item span.val { color: #0f172a; font-weight: 600; }
    .meta-box {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      border-radius: 8px;
      padding: 1rem;
      font-size: 0.875rem;
    }
    .meta-box strong { color: #1e40af; }
    code {
      background: #ffffff;
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      border: 1px solid #cbd5e1;
      font-family: monospace;
      color: #0f172a;
      font-size: 0.9em;
    }
    footer {
      margin-top: 1.25rem;
      text-align: center;
      font-size: 0.8rem;
      color: #94a3b8;
    }
  </style>
</head>
<body>
  <div class="card">
    <div class="badge">Versión: ${version}</div>
    <h1>¡Mi app corre en AWS!</h1>
    <p class="lead">Despliegue administrado en ECS Fargate con Application Load Balancer.</p>
    
    <div class="info-list">
      <div class="info-item">
        <span class="label">Proyecto:</span>
        <span class="val">RentMetrics (Data Startup)</span>
      </div>
      <div class="info-item">
        <span class="label">Alumno:</span>
        <span class="val">${alumno}</span>
      </div>
      <div class="info-item">
        <span class="label">Institución:</span>
        <span class="val">TecNM · Instituto Tecnológico de Colima</span>
      </div>
      <div class="info-item">
        <span class="label">Materia:</span>
        <span class="val">Cómputo en la Nube (IAD-2408)</span>
      </div>
    </div>

    <div class="meta-box">
      <p style="margin: 0;"><strong>Atendida por el contenedor:</strong> <code>${os.hostname()}</code></p>
      <p style="margin: 0.4rem 0 0 0; color: #475569;">Recarga con <code>Ctrl + F5</code> para verificar el balanceo entre tareas.</p>
    </div>

    <footer>
      Amazon ECR · AWS ECS Fargate · Application Load Balancer
    </footer>
  </div>
</body>
</html>`);
});

server.listen(port, () => {
  console.log(`Servidor RentMetrics escuchando en el puerto ${port}`);
});
