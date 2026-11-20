## data flow pipeline
```
experiment_runner (seed, team, dirt %, method, description size)
        | resets world, spawns robots
        v
 Gazebo world ---> world_manager (ground-truth dirt grid, floor types, scoring)
        | camera                              ^ clean(room, mode) updates dirt
        v                                     |
 perception_node (VLM) --> DirtReport         |
        |                                     |
        v                                     |
 planner_node <-- knowledge_base (apartment text + robot sheets + retriever)
   method = fullcontext | rag                 |
        | schema-constrained JSON plan        |
        v                                     |
 plan_validator --> executor (dependency gating) --> skill servers /cam /vac1 /mop1 ...
 
```

---
### problem statement related to our experiment features: 
- local models (connection to real world issue: privacy/security conscious applications make cloud models undesirable)  
-> hardware constraints: limited compute -> experiment investigates compute costs vs quality trade offs  

- especially relevant to investigate how small can a model be (on consumer grade set-ups)? which types of coordination/allocation tasks would not require frontier model level performance. specific example: household cleaning robot (use-case where concerns about security/privacy might make cloud models restricted or unacceptable [cite: GDPR for EU home data, robot-vacuum images leaking])
- RAG as candidate for equalizing compute-constrained smaller models: shifts burden of long-context attention and prefill compute on bandwidth limited iGPU (with risk of dilution) to retrieval step  
- RAG shortcoming: allocation needs global view, but retrieval is local. why not obviously better for spatial allocation  
 -> experiment investigates how context access (full context vs retrieval) results in compute/quality tradeoff during spatial task allocation   
 -> at what level of environmental complexity (dirt level + fleet coordination) as description size grows do retrieval methods become preferable?  

- general research question topic focus: how foundation model gets its context
	- full context vs retrieval as independent variables
	- semantic mapping is perception problem (how knowledge is structured), not context (how knowledge is retrieved)
		- argument: beyond scope + apt small enough unlikely to be big factor [need to find source again]  
	- example problem statement: when does retrieval help or hurt allocation quality as description size grows, and at what compute cost?  
	
- scope: 
	- project implementation: simulation, static known apt, no comparison to cloud models, foundation-model-only comparison
	- unexplored avenues of solving hardware constraint problem: other ways of cutting compute require training (quantization, distillation, prompt compression)

#### our contribution:
- multiple robot setup +  local models + full context vs retrieval   
-> context-access strategies + quality/compute trade-off + local-model task allocation + heterogeneous multi-household-robot cleaning setup  
-> possible contribution statement: "an empirical study of when retrieval over a textual environment description helps or hurts local-model task allocation for heterogeneous cleaning teams, as description size grows" [claude sonnet 5.5]

### state of the art gap:
- full context vs retrieval for single robot, not multirobot
- llm multirobot use cloud models, costs under local compute not often measured

### variables

- fleet composition (1 mop + 1 vacuum || 1 mop + 2 vacuums || 1 mop + 1 vacuum + 1 generalist
	- structural variable of capability-heterogenous constraint graph
	- allocation problem difficulty in ratio, complementarity of capabilities
- dirt
	- load variable of density of allocation problem
- perception of dirt source
	- gazebo ground truth || VLM detection

### state of the art outline:  
general framing: problem of task allocation (spatial tasks in multirobot set up)  

- classic/uncertainty aware optimization (Hungarian, MILP)  
- LLM-based allocation (grouped by architecture)  
	- centralized  
    - decentralized dialogue  
    - hybrid w solver  
    - structured world model  
    - singe centralized planner bc local hardware compute constraint. hybrid: why llm only for grounding  
    - (llm multirobot lit survey, llm for coordination, further scope?)  

- something about structured grounding? and scene-graph?
- VLM for perception, as input

- knowledge retrieval aspect of problem -> full context vs retrieval (note EmbodiedRAG single robot study)
    - who controls retrieval and when:
    - in-prompt full context
    - single retrieval
    - model-driven iterative retrieval
    - EmbodiedRAG (single robot, full-context baseline) paper
    - agentic scene-graph interface paper (we don't evaluate. reasons: extra latency per call cost on local hardware, and reports of fragility in small-model agentic loops. future work)
- investigation of compute costs vs quality (TU Wien ACIN, further scope?) by metric:
    - tokens and planning time
    - latency
    - model size sensitivity
- future work: 
    - Small-model specialization for robot planning (BTGenBot-2, PRISM), to position local models as a trend
---
### Open Questions  

~~- mac environment~~  
- evaluation metrics, configs  
~~- scene graphs and semantic mapping~~  

-  todos for sunday
	- ~~3d scene graph and world models~~  
    - problem definition (point 3)  
    - II: state of the art reorganization based on methods  
    - adding frameworks, SW packages, and underlying methods to III  
    - evaluation metrics  
   
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