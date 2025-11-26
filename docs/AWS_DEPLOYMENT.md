# Guía de Despliegue en AWS

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                         VPC                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────┐   │
│  │    Subred Pública       │  │    Subred Privada       │   │
│  │                         │  │                         │   │
│  │  ┌─────────────────┐    │  │  ┌─────────────────┐    │   │
│  │  │   EC2 Backend   │    │  │  │   RDS MySQL     │    │   │
│  │  │   (t2.micro)    │────┼──┼──│   (db.t3.micro) │    │   │
│  │  │                 │    │  │  │                 │    │   │
│  │  │  - Django       │    │  │  └─────────────────┘    │   │
│  │  │  - Uvicorn(ASGI)│    │  │                         │   │
│  │  │  - Nginx        │    │  │                         │   │
│  │  │  - Redis        │    │  │                         │   │
│  │  │  - Celery       │    │  │                         │   │
│  │  └─────────────────┘    │  │                         │   │
│  │                         │  │                         │   │
│  │  ┌─────────────────┐    │  │                         │   │
│  │  │   EC2 Frontend  │    │  │                         │   │
│  │  │   (t2.micro)    │    │  │                         │   │
│  │  └─────────────────┘    │  │                         │   │
│  └─────────────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Requisitos Previos

1. Cuenta de AWS con acceso a la capa gratuita
2. VPC configurada con subredes públicas y privadas
3. Par de claves SSH para acceso a EC2

---

## Paso 1: Crear RDS MySQL

### 1.1 Ir a RDS Console
- Servicio: **RDS** → **Create database**

### 1.2 Configuración
| Campo | Valor |
|-------|-------|
| Engine | MySQL |
| Version | 8.0.x |
| Template | **Free tier** |
| DB instance identifier | `apibackend-db` |
| Master username | `admin` |
| Master password | Tu password seguro |
| DB instance class | `db.t3.micro` (Free tier) |
| Storage | 20 GB gp2 |
| VPC | Tu VPC |
| Subnet group | Crear nuevo (subredes privadas) |
| Public access | **No** |
| VPC security group | Crear nuevo: `rds-sg` |
| Database name | `api_db` |

### 1.3 Security Group de RDS (`rds-sg`)
| Type | Protocol | Port | Source |
|------|----------|------|--------|
| MySQL/Aurora | TCP | 3306 | `ec2-sg` (SG del EC2) |

---

## Paso 2: Crear EC2 Backend

### 2.1 Ir a EC2 Console
- Servicio: **EC2** → **Launch instance**

### 2.2 Configuración
| Campo | Valor |
|-------|-------|
| Name | `apibackend-server` |
| AMI | Ubuntu Server 22.04 LTS |
| Instance type | `t2.micro` (Free tier) |
| Key pair | Tu par de claves |
| VPC | Tu VPC |
| Subnet | **Subred pública** |
| Auto-assign public IP | Enable |
| Security group | Crear nuevo: `ec2-sg` |

### 2.3 Security Group del EC2 (`ec2-sg`)
| Type | Protocol | Port | Source |
|------|----------|------|--------|
| SSH | TCP | 22 | Tu IP |
| HTTP | TCP | 80 | 0.0.0.0/0 |
| HTTPS | TCP | 443 | 0.0.0.0/0 |

### 2.4 User Data (Opcional - Despliegue automático)
Copiar el contenido de `scripts/deploy_ec2_userdata.sh` y **modificar las variables**:
- `RDS_HOST`: Endpoint de tu RDS
- `RDS_PASSWORD`: Password de RDS
- `DJANGO_SECRET_KEY`: Generar una clave segura
- `OPENAI_API_KEY`: Tu API key

---

## Paso 3: Despliegue Manual (Alternativa)

### 3.1 Conectarse al EC2
```bash
ssh -i tu-clave.pem ubuntu@tu-ip-publica
```

### 3.2 Clonar repositorio
```bash
cd /home/ubuntu
git clone -b prod https://github.com/bp-05/APIprojectBackend.git
cd APIprojectBackend
```

### 3.3 Configurar variables de entorno
```bash
cp .env.prod.example .env.prod
nano .env.prod
```

Editar con tus valores reales:
```env
MYSQL_HOST=tu-endpoint-rds.us-east-1.rds.amazonaws.com
MYSQL_PASSWORD=tu-password-rds
SECRET_KEY=genera-una-clave-secreta
OPENAI_API_KEY=tu-api-key
```

### 3.4 Ejecutar script de despliegue
```bash
chmod +x scripts/deploy_ec2_manual.sh
./scripts/deploy_ec2_manual.sh
```

---

## Paso 4: Verificación

### 4.1 Verificar servicios
```bash
sudo supervisorctl status
```

Deberías ver:
```
apibackend:celery_beat     RUNNING
apibackend:celery_worker   RUNNING
apibackend:uvicorn         RUNNING
```

### 4.2 Verificar logs
```bash
# Uvicorn (servidor ASGI)
sudo tail -f /var/log/gunicorn/uvicorn.log

# Celery
sudo tail -f /var/log/gunicorn/celery_worker.log

# Nginx
sudo tail -f /var/log/nginx/error.log
```

### 4.3 Probar endpoints
```bash
# Health check
curl http://localhost/api/

# Admin
curl http://localhost/admin/
```

---

## Comandos Útiles

### Reiniciar servicios
```bash
sudo supervisorctl restart apibackend:*
sudo systemctl restart nginx
```

### Actualizar código
```bash
cd /home/ubuntu/APIprojectBackend
git pull origin prod
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo supervisorctl restart apibackend:*
```

### Ver estado de Redis
```bash
redis-cli ping
```

### Crear nuevo superusuario
```bash
cd /home/ubuntu/APIprojectBackend
source venv/bin/activate
python manage.py createsuperuser
```

---

## Troubleshooting

### Error: "Connection refused" a RDS
1. Verificar Security Group de RDS permite puerto 3306 desde EC2
2. Verificar que RDS está en subred privada de la misma VPC
3. Probar conexión: `mysql -h tu-endpoint-rds -u admin -p`

### Error: "502 Bad Gateway"
1. Verificar Uvicorn está corriendo: `sudo supervisorctl status`
2. Ver logs: `sudo tail -f /var/log/gunicorn/uvicorn.log`
3. Verificar puerto 8000: `curl http://localhost:8000`

### Error: "Static files not found"
```bash
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart nginx
```

### Memoria insuficiente (OOM)
Si el t2.micro se queda sin memoria:
```bash
# Crear swap de 1GB
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Costos Estimados (Capa Gratuita)

| Servicio | Free Tier | Después |
|----------|-----------|---------|
| EC2 t2.micro | 750 hrs/mes | ~$8/mes |
| RDS db.t3.micro | 750 hrs/mes | ~$12/mes |
| EBS 30GB | 30 GB | ~$3/mes |
| **Total** | **$0** (12 meses) | **~$23/mes** |

---

## Próximos Pasos

1. [ ] Configurar dominio con Route 53
2. [ ] Instalar certificado SSL con Let's Encrypt
3. [ ] Configurar backups automáticos de RDS
4. [ ] Configurar CloudWatch para monitoreo
5. [ ] Desplegar frontend en segundo EC2 o S3+CloudFront
