## Open Questions  
- mac environment
- evaluation metrics, configs
- scene graphs and semantic mapping?
- todos for sunday
    - 3d scene graph and world models
    - problem definition (point 3)
    - II: state of the art reorganization based on methods
    - adding frameworks, SW packages, and underlying methods to III
    - evaluation metrics
   

## updates 
- during deployment: mini pc for inference, laptop for sim
- different repo structure
- timeline

## repo:  
swarm-cleaning/  
├── src/  
│ ├── rag_interfaces/ # Shared .srv/.msg contract (both machines)  
│ ├── sim_bringup/ # Gazebo world, robot spawning (laptop)  
│ ├── turtlebot3_swarm/ # Robot URDFs, Nav2 config (laptop)  
│ ├── world_state/ # Gazebo → ROS 2 state extraction (laptop)  
│ ├── swarm_coordination/ # Task allocation, mission monitor (laptop)  
│ ├── rag_inference/ # RAG node, KB, prompt builder (mini PC)  
│ └── llm_backend/ # LLM service wrapper (mini PC)  
├── config/  
│ ├── network\.env\.example # ROS_DOMAIN_ID, discovery settings  
│ ├── machine_sim\.yaml\.example  
│ └── machine_inference\.yaml\.example  
├── scripts/  
│ ├── setup_sim\.sh # Build sim-side packages only  
│ ├── setup_inference\.sh # Build inference-side packages only  
│ └── run_experiment\.sh # Parameterized experiment runner  
├── docs/  
│ ├── architecture\.md  
│ └── evaluation\.md  
├── .gitignore  
└── README\.md  

#### mac options

| Solution | Resource Overhead | Configuration Complexity | Communication Reliability |  
|----------|-------------------|--------------------------|---------------------------|
| **Docker + Discovery Server** | Low (container) | Medium (requires configuring Server IP) | High (unicast, not affected by multicast) |
| **Docker + `--network host`** | Low | Low | Uncertain (macOS behavior requires testing) |
| **Linux Virtual Machine (Vagrant/VMware)** | High (complete OS) | Medium | High (Linux-to-Linux, conventional configuration) |

##### if dockerized, repo:  

swarm-cleaning-rag/  
├── src/                          # Unchanged: ROS 2 packages  
│   ├── rag_interfaces/  
│   ├── sim_bringup/  
│   ├── turtlebot3_swarm/  
│   ├── world_state/  
│   ├── swarm_coordination/  
│   ├── rag_inference/  
│   └── llm_backend/  
├── docker/                       # NEW: containerization layer  
│   ├── sim/  
│   │   ├── Dockerfile            # Jazzy + Gazebo + Nav2 (Mac side)  
│   │   └── entrypoint\.sh  
│   ├── inference/  
│   │   ├── Dockerfile            # Jazzy + llama_ros + ChromaDB client (mini PC)  
│   │   └── entrypoint\.sh  
│   └── discovery/  
│       └── Dockerfile            # Optional: Discovery Server container  
├── docker-compose\.sim\.yml        # NEW: Mac-side compose (sim container)  
├── docker-compose\.inference\.yml  # NEW: mini-PC compose (inference container)  
├── config/  
│   ├── network\.env\.example  
│   ├── machine_sim\.yaml\.example  
│   ├── machine_inference\.yaml\.example  
│   └── dds/                      # NEW: DDS/Discovery Server configs  
│       ├── discovery_client\.xml  # Used inside containers  
│       └── discovery_server\.xml  
├── scripts/  
│   ├── setup_sim\.sh  
│   ├── setup_inference\.sh  
│   ├── run_experiment\.sh  
│   ├── docker_build\.sh           # NEW  
│   └── docker_run\.sh             # NEW  
├── docs/  
│   ├── architecture\.md  
│   └── evaluation\.md  
├── .gitignore                    # Updated: ignore Docker volumes, model caches  
└── README\.md                     # Updated: build/run instructions per machine  

## timeline  
- roughly **70–80% of development happens separately**
- two machines are only required on the same network during integration, deployment, and performance measurement 

#### Phase 1 — Network Foundation & Repository Setup (Week 1)
- Initialize monorepo with `src/`, `docker/`, `config/dds/`, and compose files
- Set up ROS 2 Jazzy on the mini PC (native Ubuntu 24.04) and on the Mac (Docker container or Linux VM)
- Configure DDS Discovery Server or `ROS_STATIC_PEERS`; run talker/listener discovery test across machines
- Verify `ros2 topic list` and a simple service call succeed cross-machine

**Deliverable:** Both machines see each other's ROS 2 graph reliably.

#### Phase 2 — Basic RAG-Only Prototype (Weeks 2–3, separate dvlp)
- Define `rag_interfaces` (`DescribeEnvironment.srv`, `WorldState.msg`, `CleaningEvent.msg`)
- Build `world_state_publisher` on the Mac side; verify `/world_state` topic locally
- Build `rag_node` and `llm_backend` on the Mac with a small CPU model (e.g., Qwen2.5-1.5B Q4)
- Mock the RAG service locally; validate end-to-end retrieve→generate on the Mac
- Write unit tests for prompt construction and retrieval logic

**Deliverable:** Full RAG pipeline runs on the Mac in isolation.


#### Phase 3 — Cross-Machine Integration & Vector Retrieval (Weeks 4–5)
- Connect both machines on the same network; validate `WorldState` round-trip
- Replace in-memory store with ChromaDB (HTTP mode) on the inference side
- Add embedding model; keep `DescribeEnvironment.srv` interface stable
- Develop and test on Mac; then deploy to mini PC
- Measure baseline network latency and retrieval latency

**Deliverable:** Cross-machine retrieval-augmented query succeeds end-to-end. **Week 5 gate: earliest cross-machine RAG result.**

#### Phase 4 — GPU Deployment & Classic RAG Planner (Weeks 6–7)
- Build `llama_ros` with Vulkan backend on the mini PC (780M acceleration)
- Switch to a larger quantized model (e.g., Gemma 26B Q4); measure tokens/s and latency
- Implement `rag_mode` parameter (`classic` / `agentic`) in launch files
- Implement classic RAG one-shot planner and the degraded-retrieval ablation
- Implement offline optimal allocation (Hungarian) for optimality-gap reference
- Instrument mission monitor: coverage, dirt removal, makespan, replan count, idle time

**Deliverable:** First classic RAG cleaning run with preliminary metrics. **Week 6 gate: earliest meaningful preliminary cleaning result.**

#### Phase 5 — Agentic Loop & Experiment Harness (Weeks 8–9)
- Write `run_experiment.sh` for parameterized factorial runs (N × capability × strategy × rag_mode × seed)
- Add scene graph builder (subscribes to `/world_state`) and `QuerySceneGraph.srv`
- Enable autonomous, iterative retrieval in the swarm planning loop
- Robots write `CleaningEvent` updates back to the KB
- Integrate dynamic replanning on failure or new dirt discovery

**Deliverable:** Agentic RAG operational; two-way comparison (classic vs. agentic) plus ablation ready. **Week 9 gate: near-final comparison results.**

#### Phase 6 — Evaluation & Write-Up (Week 10)
- Run full factorial experiments (10 seeds per condition)
- Statistical analysis (paired t-test / ANOVA, effect size, optimality gap)
- Produce plots (box plots, Pareto frontiers, coverage-over-time)
- Document architecture, results, and lessons learned in `docs/`

**Deliverable:** Reproducible experiment results and final report.

---

#### Key Checkpoints

| Checkpoint | Week | What You Get | Is It a Cleaning Run? |
|------------|------|--------------|------------------------|
| Cross-machine RAG query succeeds | End of Week 5 | Live Gazebo state → RAG service → description, across network | No (pipeline validation) |
| First classic RAG cleaning run | End of Week 6 | Coverage, dirt removal, makespan for classic RAG + ablation | **Yes (preliminary)** |
| Full classic vs. agentic comparison | End of Week 9 | Two-way comparison with statistics | Yes (near-final) |

---

#### Key Dependencies

| Component | Package / Tool | Machine |
|-----------|---------------|---------|
| Simulation | Gazebo Harmonic, `ros_gz_bridge` | Mac (container or VM) |
| Navigation | Nav2 | Mac (container or VM) |
| Robot model | `turtlebot3_gazebo`, custom URDF | Mac (container or VM) |
| LLM runtime | `llama_ros` (Vulkan backend) | Mini PC |
| Vector DB | ChromaDB (HTTP mode) | Mini PC |
| Embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Mini PC |
| Discovery | DDS Discovery Server / `ROS_STATIC_PEERS` | Both |
| Interfaces | Custom `.srv` / `.msg` | Both |

---

## Notes

- **Clock consistency:** Use `use_sim_time` on simulation-side nodes. Inference-side timestamps are for logging only; not used in control loops.
- **Latency boundary:** Never route velocity commands or collision-avoidance logic through the inference machine. Only high-level planning queries cross the network.
- **Fallback:** If ROCm is unstable on the 780M, use the Vulkan backend with `llama.cpp` (`HSA_OVERRIDE_GFX_VERSION=11.0.0` is the ROCm workaround if attempted).
- **Mac networking:** If native macOS DDS discovery proves flaky, escalate to Docker + Discovery Server or a Linux VM (`rosmac`-style) within 2–3 days. Do not spend more than 3 days on macOS network debugging.