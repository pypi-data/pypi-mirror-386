# DSF Quantum SDK

Reduce costos y complejidad en evaluación de inferencias cuánticas mediante simulación adaptativa y compilación inteligente.
Ejecuta y valida workloads híbridos 10× más rápido con mínima sobrecarga.

## 🚀 Why DSF Quantum?

Los entornos cuánticos tradicionales requieren acceso costoso a hardware QPU y tiempos de espera prolongados.
DSF Quantum SDK encapsula la lógica de evaluación, simulación y compilación en una capa unificada que permite:

- Simular, evaluar y compilar circuitos cuánticos desde código Python o remoto.
- Reducir pruebas reales en hardware mediante simuladores inteligentes.
- Optimizar pipelines híbridos con inferencias aceleradas en CPU/GPU.

## 📚 Core Concepts

- **Adaptive Simulation** – Ejecuta circuitos cuánticos de forma incremental con reducción adaptativa de ruido.
- **Config-as-topology** – Define tus qubits, compuertas y prioridades en forma declarativa.
- **Quantum Compilation** – Convierte circuitos de alto nivel en representaciones optimizadas (QASM, Tensor, o BinaryGraph).
- **Hybrid Evaluation** – Conecta resultados clásicos y cuánticos dentro de un mismo pipeline.
- **Enterprise**: incluye soporte para "quantum workers" distribuidos y compilación hacia hardware real o simuladores especializados.

## 📦 Installation

```bash
pip install dsf-quantum-sdk
```

Opcionalmente, apunta el SDK hacia tu backend:

```python
import os
from dsf_quantum_sdk import QuantumSDK

sdk = QuantumSDK(
    base_url=os.getenv("DSF_QUANTUM_BASE_URL"),  # e.g. https://dsf-quantum-api.vercel.app
    tier="community"
)
```

## 🎯 Quick Start

### Community

```python
from dsf_quantum_sdk import QuantumSDK

sdk = QuantumSDK()  # tier community por defecto

# Crear un circuito básico
circuit = sdk.create_circuit()
circuit.add_qubit('q0')
circuit.add_gate('H', targets=['q0'])
circuit.add_measure('q0')

# Simular localmente
result = sdk.simulate(circuit)
print("Probabilidades:", result['probabilities'])
```

### Professional

```python
from dsf_quantum_sdk import QuantumSDK

sdk = QuantumSDK(license_key="PRO-2026-12-31-XXXX", tier="professional")

circuit = (sdk.create_circuit()
    .add_qubit('q0')
    .add_qubit('q1')
    .add_gate('H', targets=['q0'])
    .add_gate('CX', targets=['q0','q1'])
    .add_measure('q0')
    .add_measure('q1')
)

# Evaluar en batch (hasta 1000 simulaciones)
experiments = [circuit.to_dict() for _ in range(10)]
scores = sdk.batch_simulate(experiments)
print("Resultados batch:", scores)
```

### Enterprise

```python
from dsf_quantum_sdk import QuantumSDK

sdk = QuantumSDK(license_key="ENT-2026-12-31-XXXX", tier="enterprise")

# Compilación + ejecución híbrida
circuit = (sdk.create_circuit()
    .add_qubit('q0')
    .add_qubit('q1')
    .add_gate('H', targets=['q0'])
    .add_gate('CX', targets=['q0','q1'])
    .add_measure('q0')
    .add_measure('q1')
)

compiled = sdk.compile(circuit, target="qasm")
hybrid_result = sdk.hybrid_run(compiled, classical_inputs={"alpha": 0.7})
print("Resultado híbrido:", hybrid_result)
```

## 🧠 Advanced Pipelines

### Quantum Worker Orchestration (Enterprise)

Permite ejecutar simulaciones o evaluaciones distribuidas en workers configurados en la nube (GCP, AWS, Vercel, etc.):

```python
task = sdk.worker_submit(
    circuit=circuit,
    backend="gcr.io/dsf-quantum-475822/quantum-worker",
    batch_size=50
)
print("Tarea enviada:", task["id"])
```

Puedes monitorear progreso:

```python
status = sdk.worker_status(task["id"])
print(status)
```

## 🔧 Fine-Tuned Recipes

### A) Community — Simple Superposition

```python
circuit = (sdk.create_circuit()
    .add_qubit('q0')
    .add_gate('H', targets=['q0'])
    .add_measure('q0')
)
result = sdk.simulate(circuit)
print(result['probabilities'])
```

### B) Professional — Entanglement Test

```python
circuit = (sdk.create_circuit()
    .add_qubit('q0').add_qubit('q1')
    .add_gate('H', targets=['q0'])
    .add_gate('CX', targets=['q0','q1'])
    .add_measure('q0').add_measure('q1')
)
sim = sdk.batch_simulate([circuit.to_dict()]*100)
print("Promedio correlación:", sum(x["correlation"] for x in sim)/100)
```

### C) Enterprise — Hybrid Workflow

```python
cfg = {"iterations": 3, "noise_level": 0.01}
hybrid = sdk.hybrid_run(circuit, classical_inputs=cfg)
print("Output:", hybrid)
```

## ⚡ Performance Tips

- Usa `batch_simulate()` en lugar de `simulate()` para grandes volúmenes.
- `compile()` puede cachearse para reutilizar topologías.
- Usa `worker_submit()` para ejecutar tareas en paralelo.
- `hybrid_run()` acepta datos clásicos para reducir overhead cuántico.

## 💡 Use Cases

### 1. Quantum Evaluation

Evalúa múltiples variantes de un circuito para analizar estabilidad y fidelidad:

```python
scores = sdk.batch_simulate([circuit.to_dict() for _ in range(500)])
```

### 2. Hybrid Optimization

Integra valores clásicos y cuánticos:

```python
result = sdk.hybrid_run(circuit, classical_inputs={"alpha": 0.5, "beta": 0.9})
```

### 3. Distributed Compilation

Despliega compilaciones pesadas a workers remotos:

```python
sdk.worker_submit(circuit, backend="gcr.io/dsf-quantum-475822/quantum-worker")
```

## 📊 Rate Limits

|      Tier    | Simulations/Day | Batch Size | Worker Jobs | Compilation |
|--------------|-----------------|------------|-------------|-------------|
| Community    |       500       |      ❌    |     ❌     |     ❌      |
| Professional |     ilimitado   |  ✅ ≤1000  |  limitado   |     ✅      |
| Enterprise   |     ilimitado   |  ✅ ≤1000  |     ✅     | ✅ (QPU)     |

## 🆚 Tier Comparison

|       Feature       | Community | Professional | Enterprise |
|---------------------|-----------|--------------|------------|
| Local simulation    |    ✅     |      ✅     |     ✅     |
| Batch simulation    |    ❌     |      ✅     |     ✅     |
| Quantum compilation |    ❌     |      ✅     | ✅ (QPU+)  |
| Hybrid evaluation   |    ❌     |      ✅     |     ✅     |
| Distributed workers |    ❌     |      ❌     |     ✅     |
| Cloud orchestration |    ❌     |      ❌     |     ✅     |

## 📖 API Reference

### Initialization

```python
QuantumSDK(
    tier='community'|'professional'|'enterprise',
    license_key=None,
    base_url=None,
    timeout=30
)
```

### Core Methods

- `create_circuit()` → Crea una nueva topología.
- `simulate(circuit)` → Simula localmente.
- `batch_simulate(circuits)` → Simula múltiples circuitos.
- `compile(circuit, target="qasm"|"binary"|"tensor")` → Compila el circuito.
- `hybrid_run(circuit, classical_inputs)` → Evalúa circuito con datos clásicos.
- `worker_submit(circuit, backend, batch_size)` → Envío distribuido.
- `worker_status(task_id)` → Monitorea progreso.

## ⚠️ Common Errors

|         Código         |           Causa            |            Solución          |
|------------------------|----------------------------|------------------------------|
| 422 Invalid Circuit    | Falta topología o medida   | Añade al menos una medida    |
| 429 Rate Limit         | Excediste el límite diario | Espera o sube de tier        |
| 500 Worker Unavailable | El worker no responde      | Reintenta o usa otro backend |
