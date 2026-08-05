"""
Analisis Jejaring Sosial - Organisasi Kemahasiswaan
Pipeline lengkap: generasi graf sintetis realistis (scale-free + small-world),
sentralitas, karakteristik global, deteksi komunitas (Louvain), simulasi SIR,
dan ekspor visualisasi + GEXF.
"""
import random
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from networkx.algorithms.community import louvain_communities, modularity
import json
import os

random.seed(42)
np.random.seed(42)

OUT = "/home/claude/work/outputs"
os.makedirs(OUT, exist_ok=True)
os.makedirs(f"{OUT}/figures", exist_ok=True)
os.makedirs(f"{OUT}/data", exist_ok=True)

# ---------------------------------------------------------------------
# 0. NAMA & DIVISI FIKTIF UNTUK NARASI ORGANISASI KEMAHASISWAAN
# ---------------------------------------------------------------------
FIRST_NAMES = ["Ahmad","Budi","Citra","Dewi","Eka","Fajar","Gita","Hadi","Indah","Joko",
    "Kartika","Lukman","Maya","Nadia","Oki","Putri","Rian","Sari","Taufik","Umi",
    "Vina","Wahyu","Yusuf","Zahra","Agus","Bella","Cahyo","Dian","Erlangga","Fitri",
    "Galih","Hana","Irfan","Julia","Kevin","Laila","Miko","Nia","Oscar","Prita",
    "Qori","Rangga","Sinta","Teguh","Uci","Vera","Wulan","Yoga","Zaki","Anisa",
    "Bagas","Clara","Doni","Elvina","Farhan","Gilang","Hafiz","Ika","Jihan","Krisna",
    "Lina","Marco","Nabila","Omar","Puput","Qonita","Reza","Salma","Tio","Ulfa",
    "Vito","Winda","Xena","Yulia","Zidan","Aditya","Bunga","Chandra","Diva","Eko",
    "Farah","Gilbert","Halim","Ira","Jamal","Kirana","Leo","Melati","Nanda","Opik",
    "Panji","Qadir","Ratna","Surya","Tania","Usman","Vania","Wisnu","Xaverius","Yudha"]
LAST_NAMES = ["Pratama","Wijaya","Santoso","Kusuma","Ramadhan","Saputra","Nugroho","Utami",
    "Setiawan","Hidayat","Permata","Firmansyah","Anggraini","Susanto","Maulana",
    "Handayani","Prasetyo","Lestari","Gunawan","Rahayu","Wibowo","Kurniawan","Puspita",
    "Yulianto","Iskandar","Suryadi","Halim","Junaedi","Kusnadi","Mardiana","Rusdianto",
    "Sinaga","Tampubolon","Simanjuntak","Halawa","Manurung","Siregar","Nasution","Batubara"]

DIVISI_LABELS = ["Kesekretariatan","Keuangan","Hubungan Masyarakat","Pengembangan SDM",
    "Minat & Bakat","Penelitian & Keilmuan","Media & Kreatif","Acara & Kegiatan"]

def random_name(used):
    for _ in range(300):
        n = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if n not in used:
            used.add(n)
            return n
    # ruang nama dasar habis (sangat jarang) -> tambahkan nama tengah, bukan angka,
    # agar hasilnya tetap terlihat seperti nama asli
    for _ in range(3000):
        n = f"{random.choice(FIRST_NAMES)} {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if n not in used:
            used.add(n)
            return n
    raise RuntimeError("Ruang nama habis")

# ---------------------------------------------------------------------
# 1. BANGUN GRAF SINTETIS (Powerlaw Cluster Graph -> scale-free + small-world)
# ---------------------------------------------------------------------
N = 1200      # jumlah anggota (node)
M = 3         # edge baru per node (preferential attachment)
P_TRIANGLE = 0.15  # probabilitas closing triangle -> clustering tinggi (small-world)

G = nx.powerlaw_cluster_graph(N, M, P_TRIANGLE, seed=42)

# Bobot edge = intensitas komunikasi (jumlah interaksi/bulan), didistribusikan
# tidak merata untuk merepresentasikan variasi intensitas komunikasi riil.
for u, v in G.edges():
    w = int(np.random.lognormal(mean=1.3, sigma=0.9))
    G[u][v]["weight"] = max(1, min(w, 60))

# Buang node isolate (jika ada) agar graf representatif sbg jejaring komunikasi
G.remove_nodes_from(list(nx.isolates(G)))
print(f"Jumlah node setelah pembersihan: {G.number_of_nodes()}")
print(f"Jumlah edge: {G.number_of_edges()}")

# ---------------------------------------------------------------------
# 2. SENTRALITAS
# ---------------------------------------------------------------------
deg_cent = nx.degree_centrality(G)
between_cent = nx.betweenness_centrality(G, k=400, seed=42, weight="weight")
close_cent = nx.closeness_centrality(G)
eig_cent = nx.eigenvector_centrality(G, max_iter=2000, weight="weight")

def top_n(d, n=10):
    return sorted(d.items(), key=lambda x: x[1], reverse=True)[:n]

top_deg = top_n(deg_cent)
top_bet = top_n(between_cent)
top_clo = top_n(close_cent)
top_eig = top_n(eig_cent)

# ---------------------------------------------------------------------
# 3. KARAKTERISTIK GLOBAL
# ---------------------------------------------------------------------
density = nx.density(G)
largest_cc_nodes = max(nx.connected_components(G), key=len)
G_lcc = G.subgraph(largest_cc_nodes).copy()
diameter = nx.diameter(G_lcc)
avg_path_len = nx.average_shortest_path_length(G_lcc)
avg_clustering = nx.average_clustering(G)
lcc_fraction = len(largest_cc_nodes) / G.number_of_nodes()

degrees = [d for _, d in G.degree()]
avg_degree = np.mean(degrees)

# Random graph pembanding (Erdos-Renyi) dengan N, E setara -> uji small-world
E = G.number_of_edges()
G_rand = nx.gnm_random_graph(G.number_of_nodes(), E, seed=42)
rand_clustering = nx.average_clustering(G_rand)
try:
    rand_lcc = max(nx.connected_components(G_rand), key=len)
    G_rand_lcc = G_rand.subgraph(rand_lcc)
    rand_path_len = nx.average_shortest_path_length(G_rand_lcc)
except Exception:
    rand_path_len = float("nan")

# ---------------------------------------------------------------------
# 4. DETEKSI KOMUNITAS (LOUVAIN)
# ---------------------------------------------------------------------
communities = louvain_communities(G, weight="weight", seed=42, resolution=1.0)
Q = modularity(G, communities, weight="weight")
num_communities = len(communities)

node_community = {}
for i, com in enumerate(communities):
    for node in com:
        node_community[node] = i

# ---------------------------------------------------------------------
# 5. ATRIBUT NARATIF (nama, peran, divisi) — dipasangkan berdasar struktur graf
# ---------------------------------------------------------------------
used_names = set()
names = {}
for node in G.nodes():
    names[node] = random_name(used_names)

# peran berbasis peringkat gabungan sentralitas (bukan acak) agar bermakna
combined_score = {n: deg_cent[n] + between_cent[n] + eig_cent[n] for n in G.nodes()}
ranked_nodes = sorted(combined_score.items(), key=lambda x: x[1], reverse=True)

roles = {}
roles[ranked_nodes[0][0]] = "Ketua Umum"
roles[ranked_nodes[1][0]] = "Wakil Ketua"
roles[ranked_nodes[2][0]] = "Sekretaris Umum"
roles[ranked_nodes[3][0]] = "Bendahara Umum"

# koordinator per komunitas = node dengan degree tertinggi di komunitas tsb
community_list = sorted(communities, key=len, reverse=True)
for i, com in enumerate(community_list):
    if i >= len(DIVISI_LABELS):
        break
    candidates = [n for n in com if n not in roles]
    if not candidates:
        continue
    coord = max(candidates, key=lambda n: deg_cent[n])
    roles[coord] = f"Koordinator Divisi {DIVISI_LABELS[i]}"

for node in G.nodes():
    if node not in roles:
        roles[node] = "Anggota"

for i, com in enumerate(community_list):
    label = DIVISI_LABELS[i] if i < len(DIVISI_LABELS) else f"Kelompok-{i+1}"
    for n in com:
        G.nodes[n]["divisi"] = label
    for n in com:
        G.nodes[n]["community_id"] = i

for node in G.nodes():
    G.nodes[node]["label"] = names[node]
    G.nodes[node]["role"] = roles[node]
    G.nodes[node]["degree_centrality"] = round(deg_cent[node], 4)
    G.nodes[node]["betweenness_centrality"] = round(between_cent[node], 4)
    G.nodes[node]["closeness_centrality"] = round(close_cent[node], 4)
    G.nodes[node]["eigenvector_centrality"] = round(eig_cent[node], 4)

# ---------------------------------------------------------------------
# 6. SIMPAN RINGKASAN TOP-10 (dengan nama & peran) KE JSON
# ---------------------------------------------------------------------
def enrich(top_list):
    return [{"node": int(n), "nama": names[n], "peran": roles[n], "divisi": G.nodes[n]["divisi"], "skor": round(v,4)} for n, v in top_list]

summary = {
    "n_nodes": G.number_of_nodes(),
    "n_edges": G.number_of_edges(),
    "avg_degree": round(avg_degree, 3),
    "density": round(density, 6),
    "diameter_lcc": diameter,
    "avg_path_length_lcc": round(avg_path_len, 4),
    "avg_clustering": round(avg_clustering, 4),
    "lcc_fraction": round(lcc_fraction, 4),
    "random_graph_clustering": round(rand_clustering, 5),
    "random_graph_avg_path_length": round(rand_path_len, 4),
    "num_communities": num_communities,
    "modularity_Q": round(Q, 4),
    "top_degree": enrich(top_deg),
    "top_betweenness": enrich(top_bet),
    "top_closeness": enrich(top_clo),
    "top_eigenvector": enrich(top_eig),
}
with open(f"{OUT}/data/summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2)[:3000])

# ---------------------------------------------------------------------
# 7. VISUALISASI
# ---------------------------------------------------------------------
plt.style.use("default")
COLORS = plt.cm.tab10.colors

# 7a. Distribusi Degree (log-log) -> menunjukkan pola scale-free
fig, ax = plt.subplots(figsize=(7,5))
deg_values, deg_counts = np.unique(degrees, return_counts=True)
ax.scatter(deg_values, deg_counts, color="#2563eb", alpha=0.75)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Degree (log)"); ax.set_ylabel("Jumlah Node (log)")
ax.set_title("Distribusi Degree Jejaring Organisasi (Pola Scale-Free)")
plt.tight_layout()
plt.savefig(f"{OUT}/figures/01_degree_distribution.png", dpi=200)
plt.close()

# 7b. Bar chart top-10 tiap metrik
fig, axes = plt.subplots(2, 2, figsize=(13, 9))
metrics = [("Degree Centrality", top_deg, "#2563eb"),
           ("Betweenness Centrality", top_bet, "#dc2626"),
           ("Closeness Centrality", top_clo, "#16a34a"),
           ("Eigenvector Centrality", top_eig, "#9333ea")]
for ax, (title, data, color) in zip(axes.flat, metrics):
    labels = [names[n][:16] for n, v in data]
    vals = [v for n, v in data]
    ax.barh(labels[::-1], vals[::-1], color=color)
    ax.set_title(f"Top-10 {title}")
    ax.tick_params(axis="y", labelsize=8)
plt.tight_layout()
plt.savefig(f"{OUT}/figures/02_top10_centrality.png", dpi=200)
plt.close()

# 7c. Visualisasi jejaring dgn komunitas (subsample untuk keterbacaan visual)
sample_size = 300
sample_nodes = set(random.sample(list(G.nodes()), min(sample_size, G.number_of_nodes())))
# pastikan node top-10 gabungan ikut tampil
key_nodes = set(n for n,_ in (top_deg+top_bet+top_eig))
sample_nodes |= key_nodes
G_sample = G.subgraph(sample_nodes).copy()
G_sample.remove_nodes_from(list(nx.isolates(G_sample)))

pos = nx.spring_layout(G_sample, seed=42, k=0.25)
fig, ax = plt.subplots(figsize=(11, 9))
node_colors = [COLORS[G_sample.nodes[n]["community_id"] % 10] for n in G_sample.nodes()]
node_sizes = [50 + 3000 * deg_cent[n] for n in G_sample.nodes()]
nx.draw_networkx_edges(G_sample, pos, alpha=0.15, width=0.5, ax=ax)
nx.draw_networkx_nodes(G_sample, pos, node_color=node_colors, node_size=node_sizes, alpha=0.9, ax=ax)
top_labels = {n: names[n].split()[0] for n in key_nodes if n in G_sample}
nx.draw_networkx_labels(G_sample, pos, labels=top_labels, font_size=8, ax=ax)
ax.set_title("Visualisasi Jejaring Organisasi (sampel 300+ node) — Warna = Komunitas (Louvain), Ukuran = Degree Centrality")
ax.axis("off")
plt.tight_layout()
plt.savefig(f"{OUT}/figures/03_network_communities.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------
# 8. SIMULASI SIR (PENYEBARAN INFORMASI)
# ---------------------------------------------------------------------
def simulate_SIR(G, beta, gamma, initial_infected, steps=60):
    state = {n: "S" for n in G.nodes()}
    for n in initial_infected:
        state[n] = "I"
    S_hist, I_hist, R_hist = [], [], []
    for t in range(steps):
        S = sum(1 for v in state.values() if v == "S")
        I = sum(1 for v in state.values() if v == "I")
        R = sum(1 for v in state.values() if v == "R")
        S_hist.append(S); I_hist.append(I); R_hist.append(R)
        new_state = dict(state)
        for n in G.nodes():
            if state[n] == "I":
                for nb in G.neighbors(n):
                    if state[nb] == "S" and random.random() < beta:
                        new_state[nb] = "I"
                if random.random() < gamma:
                    new_state[n] = "R"
        state = new_state
        if I == 0 and t > 0:
            # isi sisa steps dengan nilai terakhir agar panjang array konsisten
            for _ in range(steps - len(S_hist)):
                S_hist.append(S_hist[-1]); I_hist.append(I_hist[-1]); R_hist.append(R_hist[-1])
            break
    return S_hist, I_hist, R_hist

beta, gamma = 0.06, 0.12

node_kunci = top_eig[0][0]  # node eigenvector tertinggi
low_degree_nodes = [n for n, d in G.degree() if d <= 2]
node_acak = random.choice(low_degree_nodes) if low_degree_nodes else random.choice(list(G.nodes()))

random.seed(7)
S_a, I_a, R_a = simulate_SIR(G, beta, gamma, [node_kunci])
random.seed(7)
S_b, I_b, R_b = simulate_SIR(G, beta, gamma, [node_acak])

peak_a_t = int(np.argmax(I_a)); peak_a_v = max(I_a)
peak_b_t = int(np.argmax(I_b)); peak_b_v = max(I_b)
reach_a = R_a[-1] + I_a[-1]
reach_b = R_b[-1] + I_b[-1]

sir_summary = {
    "node_kunci": {"id": int(node_kunci), "nama": names[node_kunci], "peran": roles[node_kunci]},
    "node_acak_rendah": {"id": int(node_acak), "nama": names[node_acak], "peran": roles[node_acak]},
    "skenario_A_waktu_puncak": peak_a_t, "skenario_A_puncak_infected": peak_a_v, "skenario_A_jangkauan_akhir": reach_a,
    "skenario_B_waktu_puncak": peak_b_t, "skenario_B_puncak_infected": peak_b_v, "skenario_B_jangkauan_akhir": reach_b,
}
with open(f"{OUT}/data/sir_summary.json", "w", encoding="utf-8") as f:
    json.dump(sir_summary, f, ensure_ascii=False, indent=2)
print(json.dumps(sir_summary, ensure_ascii=False, indent=2))

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
for ax, (S,I,R,title) in zip(axes, [(S_a,I_a,R_a,f"Skenario A: mulai dari {names[node_kunci]} ({roles[node_kunci]})"),
                                      (S_b,I_b,R_b,f"Skenario B: mulai dari {names[node_acak]} (Anggota, degree rendah)")]):
    ax.plot(S, label="Susceptible", color="#94a3b8")
    ax.plot(I, label="Infected (menerima info)", color="#dc2626")
    ax.plot(R, label="Recovered (info usang)", color="#16a34a")
    ax.set_title(title, fontsize=10)
    ax.set_xlabel("Waktu (step)"); ax.set_ylabel("Jumlah node")
    ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f"{OUT}/figures/04_sir_simulation.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------
# 9. EKSPOR GEXF UNTUK GEPHI
# ---------------------------------------------------------------------
G_export = G.copy()
for n in G_export.nodes():
    G_export.nodes[n]["community_id"] = int(G_export.nodes[n]["community_id"])
nx.write_gexf(G_export, f"{OUT}/data/jejaring_organisasi.gexf")

print("\nSELESAI. Semua output tersimpan di:", OUT)
