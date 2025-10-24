# 🚀 Advanced Features - Graph Database

## 📋 Overview

Setelah implementasi dasar selesai, berikut adalah fitur-fitur advanced yang bisa ditambahkan untuk memaksimalkan potensi graph database.

---

## 1. Derived Relationships (TEMAN_SEKELAS)

### **Konsep**

Relationship `TEMAN_SEKELAS` tidak perlu di-input manual, tapi di-**derive** dari data yang sudah ada:

```
Jika: (Mahasiswa A)-[:MENGAMBIL]->(Kelas X)<-[:MENGAMBIL]-(Mahasiswa B)
Maka: (Mahasiswa A)-[:TEMAN_SEKELAS {kelas_bersama: 1}]->(Mahasiswa B)
```

### **Implementation**

```python
# Di graph_sync.py, tambahkan method:

def create_teman_sekelas_relationships(self):
    """Create derived TEMAN_SEKELAS relationships"""
    query = """
    MATCH (m1:MahasiswaNode)-[:MENGAMBIL]->(k:KelasNode)<-[:MENGAMBIL]-(m2:MahasiswaNode)
    WHERE m1 <> m2 AND NOT (m1)-[:TEMAN_SEKELAS]-(m2)
    WITH m1, m2, COUNT(k) as kelas_bersama
    WHERE kelas_bersama > 0
    CREATE (m1)-[:TEMAN_SEKELAS {jumlah_kelas: kelas_bersama}]->(m2)
    RETURN COUNT(*) as created
    """

    try:
        results, meta = db.cypher_query(query)
        count = results[0][0] if results else 0
        logger.info(f"Created {count} TEMAN_SEKELAS relationships")
        return count
    except Exception as e:
        logger.error(f"Error creating TEMAN_SEKELAS: {e}")
        return 0
```

### **Usage**

```bash
python manage.py shell
```

```python
from apps.academic.graph_sync import GraphSyncManager

manager = GraphSyncManager()
count = manager.create_teman_sekelas_relationships()
print(f"Created {count} TEMAN_SEKELAS relationships")
```

### **Query dengan Relationship Properties**

```cypher
// Find teman sekelas dengan jumlah kelas bersama
MATCH (m:MahasiswaNode {nim: '11201800001'})
      -[r:TEMAN_SEKELAS]->(teman)
WHERE r.jumlah_kelas >= 3
RETURN teman.nama, r.jumlah_kelas
ORDER BY r.jumlah_kelas DESC
```

---

## 2. Prerequisite Chain Analysis

### **Setup Prerequisite Data**

```python
# Di graph_sync.py
def sync_prerequisite_relationships(self):
    """Create PREREQUISITE relationships from kurikulum data"""
    from apps.feeder.models.kurikulum import MataKuliahKurikulum

    count = 0
    for mk_kurikulum in MataKuliahKurikulum.objects.filter(deleted=False):
        if not mk_kurikulum.id_matkul_prasyarat:
            continue

        try:
            # Get nodes
            mk_node = MataKuliahNode.nodes.get(
                kode=mk_kurikulum.id_matkul.kode_mata_kuliah
            )
            prereq_node = MataKuliahNode.nodes.get(
                kode=mk_kurikulum.id_matkul_prasyarat.kode_mata_kuliah
            )

            # Create relationship
            if not mk_node.prerequisite.is_connected(prereq_node):
                mk_node.prerequisite.connect(prereq_node)
                count += 1

        except Exception as e:
            logger.error(f"Error syncing prerequisite: {e}")
            continue

    logger.info(f"Created {count} PREREQUISITE relationships")
    return count
```

### **Advanced Prerequisite Queries**

#### **1. Full Prerequisite Chain**

```cypher
// Lihat semua prerequisite untuk mata kuliah tertentu
MATCH path = (mk:MataKuliahNode {kode: 'IF401'})
             -[:PREREQUISITE*]->(prereq)
RETURN path
```

#### **2. Shortest Path to Target Course**

```python
# Di graph_service.py
@staticmethod
def get_prerequisite_path(nim: str, target_kode: str):
    """Find prerequisite path for student"""
    query = """
    MATCH (m:MahasiswaNode {nim: $nim})
    MATCH (target:MataKuliahNode {kode: $target_kode})
    MATCH (m)-[:LULUS]->(:KelasNode)-[:UNTUK_MATKUL]->(completed:MataKuliahNode)
    WITH m, target, COLLECT(completed.kode) as completed_codes
    MATCH path = shortestPath(
        (start:MataKuliahNode)-[:PREREQUISITE*]->(target)
    )
    WHERE NOT start.kode IN completed_codes
    RETURN path, LENGTH(path) as depth
    ORDER BY depth
    LIMIT 1
    """

    results, meta = db.cypher_query(query, {
        'nim': nim,
        'target_kode': target_kode
    })

    if results:
        return {
            'found': True,
            'depth': results[0][1],
            'message': f"Need to complete {results[0][1]} prerequisites"
        }
    else:
        return {
            'found': False,
            'message': 'No prerequisites needed or already completed'
        }
```

#### **3. Check if Student Can Take Course**

```python
@staticmethod
def can_take_course(nim: str, kode_mk: str):
    """Check if student meets all prerequisites"""
    query = """
    MATCH (mk:MataKuliahNode {kode: $kode_mk})
    OPTIONAL MATCH (mk)-[:PREREQUISITE*]->(prereq)
    WITH mk, COLLECT(DISTINCT prereq.kode) as required

    MATCH (m:MahasiswaNode {nim: $nim})
    OPTIONAL MATCH (m)-[:LULUS]->(:KelasNode)-[:UNTUK_MATKUL]->(completed)
    WITH mk, required, COLLECT(DISTINCT completed.kode) as completed

    RETURN
        CASE
            WHEN SIZE(required) = 0 THEN true
            ELSE ALL(r IN required WHERE r IN completed)
        END as can_take,
        required,
        completed,
        [r IN required WHERE NOT r IN completed] as missing
    """

    results, meta = db.cypher_query(query, {
        'nim': nim,
        'kode_mk': kode_mk
    })

    if results:
        return {
            'can_take': results[0][0],
            'required': results[0][1] or [],
            'completed': results[0][2] or [],
            'missing': results[0][3] or []
        }
```

---

## 3. Social Network Analysis

### **1. Network Strength Score**

```python
@staticmethod
def get_network_strength(nim: str):
    """Calculate student's network strength"""
    query = """
    MATCH (m:MahasiswaNode {nim: $nim})

    // Direct connections
    OPTIONAL MATCH (m)-[:MENGAMBIL]->(:KelasNode)<-[:MENGAMBIL]-(direct)
    WHERE m <> direct
    WITH m, COUNT(DISTINCT direct) as direct_count

    // Extended network (2-hop)
    OPTIONAL MATCH (m)-[:MENGAMBIL]->(:KelasNode)<-[:MENGAMBIL]-(friend)
                      -[:MENGAMBIL]->(:KelasNode)<-[:MENGAMBIL]-(extended)
    WHERE extended <> m AND friend <> m
    WITH m, direct_count, COUNT(DISTINCT extended) as extended_count

    // Total classes
    OPTIONAL MATCH (m)-[:MENGAMBIL]->(k:KelasNode)
    WITH m, direct_count, extended_count, COUNT(k) as total_classes

    RETURN
        direct_count,
        extended_count,
        total_classes,
        (direct_count * 1.0 + extended_count * 0.5) as network_score
    """

    results, meta = db.cypher_query(query, {'nim': nim})

    if results:
        return {
            'direct_connections': results[0][0] or 0,
            'extended_network': results[0][1] or 0,
            'total_classes': results[0][2] or 0,
            'network_score': results[0][3] or 0
        }
```

### **2. Find Study Groups**

```python
@staticmethod
def suggest_study_groups(nim: str, min_kelas_bersama: int = 3):
    """Suggest study groups based on shared classes"""
    query = """
    MATCH (m:MahasiswaNode {nim: $nim})
          -[:MENGAMBIL]->(k:KelasNode)
          <-[:MENGAMBIL]-(teman)
    WHERE m <> teman
    WITH teman, COUNT(k) as kelas_bersama
    WHERE kelas_bersama >= $min_kelas
    RETURN teman.nim, teman.nama, teman.ipk, kelas_bersama
    ORDER BY kelas_bersama DESC, teman.ipk DESC
    """

    results, meta = db.cypher_query(query, {
        'nim': nim,
        'min_kelas': min_kelas_bersama
    })

    return [
        {
            'nim': row[0],
            'nama': row[1],
            'ipk': row[2],
            'kelas_bersama': row[3]
        }
        for row in results
    ]
```

### **3. Community Detection**

```cypher
// Find densely connected student groups
CALL gds.louvain.stream({
  nodeProjection: 'MahasiswaNode',
  relationshipProjection: 'TEMAN_SEKELAS'
})
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).nama as nama,
       communityId
ORDER BY communityId
```

---

## 4. Recommendation Engine

### **1. Collaborative Filtering untuk Mata Kuliah**

```python
@staticmethod
def recommend_courses_advanced(nim: str, limit: int = 10):
    """Advanced course recommendation with scoring"""
    query = """
    MATCH (m:MahasiswaNode {nim: $nim})

    // Find similar students (same angkatan, similar IPK)
    MATCH (similar:MahasiswaNode)
    WHERE similar <> m
      AND similar.angkatan = m.angkatan
      AND ABS(similar.ipk - m.ipk) < 0.5

    // Find courses they're taking
    MATCH (similar)-[:MENGAMBIL]->(k:KelasNode)-[:UNTUK_MATKUL]->(mk:MataKuliahNode)

    // Exclude courses student already took
    WHERE NOT (m)-[:MENGAMBIL]->(:KelasNode)-[:UNTUK_MATKUL]->(mk)

    // Score based on multiple factors
    WITH mk,
         COUNT(DISTINCT similar) as similar_students,
         AVG(similar.ipk) as avg_ipk,
         mk.sks as sks
    ORDER BY similar_students DESC, avg_ipk DESC
    LIMIT $limit

    RETURN
        mk.kode,
        mk.nama,
        mk.sks,
        similar_students,
        avg_ipk,
        (similar_students * 0.7 + avg_ipk * 0.3) as recommendation_score
    ORDER BY recommendation_score DESC
    """

    results, meta = db.cypher_query(query, {'nim': nim, 'limit': limit})

    return [
        {
            'kode': row[0],
            'nama': row[1],
            'sks': row[2],
            'taken_by': row[3],
            'avg_ipk': row[4],
            'score': row[5]
        }
        for row in results
    ]
```

### **2. Dosen Recommendation**

```python
@staticmethod
def recommend_dosen_pembimbing(nim: str):
    """Recommend dosen for pembimbing based on network"""
    query = """
    MATCH (m:MahasiswaNode {nim: $nim})
          -[:MENGAMBIL]->(k:KelasNode)
          <-[:MENGAJAR]-(d:DosenNode)

    // Count interactions
    WITH d, COUNT(k) as kelas_diajar

    // Find dosen's success rate (students with good IPK)
    MATCH (d)-[:MENGAJAR]->(:KelasNode)<-[:MENGAMBIL]-(mhs:MahasiswaNode)
    WITH d, kelas_diajar, AVG(mhs.ipk) as avg_student_ipk

    RETURN
        d.nip,
        d.nama,
        d.jabatan,
        kelas_diajar,
        avg_student_ipk,
        (kelas_diajar * 0.6 + avg_student_ipk * 0.4) as recommendation_score
    ORDER BY recommendation_score DESC
    LIMIT 5
    """

    results, meta = db.cypher_query(query, {'nim': nim})

    return [
        {
            'nip': row[0],
            'nama': row[1],
            'jabatan': row[2],
            'kelas_diajar': row[3],
            'avg_student_ipk': row[4],
            'score': row[5]
        }
        for row in results
    ]
```

---

## 5. Performance Optimization

### **1. Create Indexes**

```python
# Di graph_sync.py
def create_indexes(self):
    """Create Neo4j indexes for better performance"""
    indexes = [
        "CREATE INDEX mahasiswa_nim IF NOT EXISTS FOR (m:MahasiswaNode) ON (m.nim)",
        "CREATE INDEX mahasiswa_angkatan IF NOT EXISTS FOR (m:MahasiswaNode) ON (m.angkatan)",
        "CREATE INDEX dosen_nip IF NOT EXISTS FOR (d:DosenNode) ON (d.nip)",
        "CREATE INDEX matkul_kode IF NOT EXISTS FOR (mk:MataKuliahNode) ON (mk.kode)",
        "CREATE INDEX kelas_id IF NOT EXISTS FOR (k:KelasNode) ON (k.id_kelas)",
    ]

    for index_query in indexes:
        try:
            with self.driver.session() as session:
                session.run(index_query)
            logger.info(f"Created index: {index_query}")
        except Exception as e:
            logger.warning(f"Index creation failed: {e}")
```

### **2. Batch Operations**

```python
def sync_mahasiswa_batch(self, batch_size=1000):
    """Sync mahasiswa in batches"""
    total = RiwayatPendidikan.objects.filter(deleted=False).count()
    processed = 0

    for offset in range(0, total, batch_size):
        batch = RiwayatPendidikan.objects.filter(deleted=False)[offset:offset+batch_size]

        for riwayat in batch:
            self.sync_mahasiswa_node(riwayat)
            processed += 1

        logger.info(f"Processed {processed}/{total} mahasiswa")
        time.sleep(0.1)  # Prevent overload

    return processed
```

### **3. Query Caching**

```python
from functools import lru_cache
from django.core.cache import cache

@staticmethod
def get_classmates_cached(nim: str, limit: int = 50):
    """Get classmates with Redis caching"""
    cache_key = f"graph:classmates:{nim}:{limit}"

    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Query Neo4j
    result = AcademicGraphService.get_classmates(nim, limit)

    # Cache for 1 hour
    cache.set(cache_key, result, 3600)

    return result
```

---

## 6. Real-time Sync dengan Django Signals

### **Implementation**

```python
# apps/academic/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.feeder.models.mahasiswa import RiwayatPendidikan
from apps.academic.graph_sync import GraphSyncManager

@receiver(post_save, sender=RiwayatPendidikan)
def sync_mahasiswa_to_neo4j(sender, instance, created, **kwargs):
    """Auto-sync mahasiswa to Neo4j on save"""
    from django.conf import settings

    if not settings.NEO4J_ENABLE_SYNC:
        return

    try:
        manager = GraphSyncManager()
        manager.sync_mahasiswa_node(instance)
        manager.close()
    except Exception as e:
        logger.error(f"Failed to sync mahasiswa to Neo4j: {e}")
```

**Note:** Real-time sync bisa memperlambat request. Pertimbangkan gunakan Celery untuk async processing.

---

## 7. Graph Visualization

### **Export untuk Vis.js / D3.js**

```python
@staticmethod
def get_graph_visualization_data(nim: str, depth: int = 2):
    """Export graph data for visualization"""
    query = """
    MATCH path = (m:MahasiswaNode {nim: $nim})
                 -[:MENGAMBIL|TEMAN_SEKELAS*1..{depth}]-
                 (connected)
    UNWIND nodes(path) as node
    UNWIND relationships(path) as rel
    RETURN
        COLLECT(DISTINCT {
            id: id(node),
            label: COALESCE(node.nama, node.nama_kelas),
            type: labels(node)[0]
        }) as nodes,
        COLLECT(DISTINCT {
            source: id(startNode(rel)),
            target: id(endNode(rel)),
            type: type(rel)
        }) as edges
    """

    results, meta = db.cypher_query(query.replace('{depth}', str(depth)), {'nim': nim})

    if results:
        return {
            'nodes': results[0][0],
            'edges': results[0][1]
        }
    return {'nodes': [], 'edges': []}
```

### **API Endpoint untuk Visualization**

```python
class GraphVisualizationView(APIView):
    """Get graph data for visualization"""

    def get(self, request):
        nim = request.user.username
        depth = int(request.GET.get('depth', 2))

        data = AcademicGraphService.get_graph_visualization_data(nim, depth)

        return Response({
            'success': True,
            'data': data
        })
```

---

## 8. Monitoring & Maintenance

### **1. Health Check**

```python
@staticmethod
def health_check():
    """Check Neo4j health"""
    try:
        from django.conf import settings
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()

        driver.close()

        return {'status': 'healthy', 'connected': True}
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}
```

### **2. Data Consistency Check**

```python
def check_data_consistency(self):
    """Check if Neo4j data matches PostgreSQL"""
    pg_count = RiwayatPendidikan.objects.filter(deleted=False).count()
    neo4j_count = len(MahasiswaNode.nodes.all())

    return {
        'postgresql': pg_count,
        'neo4j': neo4j_count,
        'difference': abs(pg_count - neo4j_count),
        'sync_needed': pg_count != neo4j_count
    }
```

### **3. Clear Graph Database**

```python
def clear_all_data(self):
    """Clear all Neo4j data (USE WITH CAUTION!)"""
    query = "MATCH (n) DETACH DELETE n"

    with self.driver.session() as session:
        result = session.run(query)

    logger.warning("All Neo4j data cleared!")
```

---

## ✅ Best Practices

1. **Always Sync in Batches**: Jangan sync semua data sekaligus
2. **Use Indexes**: Create indexes untuk properties yang sering di-query
3. **Cache Results**: Gunakan Redis untuk cache query results
4. **Monitor Performance**: Track query execution time
5. **Regular Maintenance**: Scheduled consistency checks
6. **Graceful Degradation**: System harus tetap jalan tanpa Neo4j
7. **Backup Strategy**: Regular Neo4j backups
8. **Security**: Change default password, restrict ports

---

**Next:** [04-PRODUCTION-DEPLOYMENT.md](./04-PRODUCTION-DEPLOYMENT.md) - Deploy ke production
