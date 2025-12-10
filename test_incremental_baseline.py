"""
Script di test per il sistema di Baseline Incrementale
Testa le funzionalità principali senza bisogno di video reali
"""
import sys
import os

# Aggiungi backend al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from baseline_manager import BaselineHistory
import json
import tempfile
import shutil

def test_baseline_history():
    """Test completo del sistema BaselineHistory"""
    
    print("=" * 60)
    print("🧪 TEST BASELINE INCREMENTALE")
    print("=" * 60)
    
    # Crea directory temporanea per test
    test_dir = tempfile.mkdtemp()
    history_file = os.path.join(test_dir, 'baseline_history.json')
    ghost_folder = os.path.join(test_dir, 'ghost_frames')
    
    try:
        # Test 1: Creazione nuova baseline history
        print("\n📝 Test 1: Creazione nuova baseline history")
        bh = BaselineHistory(history_file, ghost_folder)
        history = bh.load()
        
        assert history['run_count'] == 0, "Run count dovrebbe essere 0"
        assert history['best_run_id'] is None, "Best run ID dovrebbe essere None"
        print("✅ Test 1 passato: Baseline history vuota creata correttamente")
        
        # Test 2: Aggiunta prima corsa (Ottimale)
        print("\n📝 Test 2: Aggiunta prima corsa (Ottimale)")
        analysis_data_1 = {
            'viewType': 'posterior',
            'anomaly_level': 'Ottimale',
            'anomaly_score': 0.65,
            'metrics': {
                'left_knee_valgus': {'value': 8.5, 'z_score': 0.5, 'level': 'Ottimale'},
                'right_knee_valgus': {'value': 8.2, 'z_score': 0.3, 'level': 'Ottimale'},
                'pelvic_drop': {'value': 2.4, 'z_score': 0.2, 'level': 'Ottimale'},
                'cadence': {'value': 178.0, 'z_score': -0.1, 'level': 'Ottimale'},
                'knee_valgus_symmetry': {'value': 95.0, 'z_score': 0.0, 'level': 'Ottimale'}
            }
        }
        
        result = bh.update(analysis_data_1, 'run_001')
        
        assert result['status'] == 'success', "Update dovrebbe avere successo"
        assert result['run_count'] == 1, "Run count dovrebbe essere 1"
        assert result['is_new_best'] == True, "Prima corsa dovrebbe essere la migliore"
        assert result['best_run_id'] == 'run_001', "Best run ID dovrebbe essere run_001"
        
        # Verifica statistiche globali
        assert 'left_knee_valgus' in bh.history_data['global_stats']
        assert bh.history_data['global_stats']['left_knee_valgus']['mean'] == 8.5
        
        print("✅ Test 2 passato: Prima corsa aggiunta correttamente")
        print(f"   Run count: {result['run_count']}")
        print(f"   Best run error: {result['best_run_error']:.4f}")
        
        # Test 3: Aggiunta seconda corsa (migliore)
        print("\n📝 Test 3: Aggiunta seconda corsa (migliore)")
        analysis_data_2 = {
            'viewType': 'posterior',
            'anomaly_level': 'Ottimale',
            'anomaly_score': 0.45,
            'metrics': {
                'left_knee_valgus': {'value': 8.3, 'z_score': 0.3, 'level': 'Ottimale'},
                'right_knee_valgus': {'value': 8.1, 'z_score': 0.2, 'level': 'Ottimale'},
                'pelvic_drop': {'value': 2.3, 'z_score': 0.1, 'level': 'Ottimale'},
                'cadence': {'value': 177.5, 'z_score': 0.0, 'level': 'Ottimale'},
                'knee_valgus_symmetry': {'value': 96.0, 'z_score': 0.1, 'level': 'Ottimale'}
            }
        }
        
        result = bh.update(analysis_data_2, 'run_002')
        
        assert result['run_count'] == 2, "Run count dovrebbe essere 2"
        assert result['is_new_best'] == True, "Seconda corsa dovrebbe essere la migliore"
        assert result['best_run_id'] == 'run_002', "Best run ID dovrebbe essere run_002"
        
        # Verifica media incrementale
        expected_mean = (8.5 + 8.3) / 2  # 8.4
        actual_mean = bh.history_data['global_stats']['left_knee_valgus']['mean']
        assert abs(actual_mean - expected_mean) < 0.01, f"Media dovrebbe essere ~{expected_mean}, ma è {actual_mean}"
        
        print("✅ Test 3 passato: Seconda corsa aggiunta, è la nuova migliore")
        print(f"   Run count: {result['run_count']}")
        print(f"   Best run error: {result['best_run_error']:.4f}")
        print(f"   Media left_knee_valgus: {actual_mean:.2f}°")
        
        # Test 4: Aggiunta terza corsa (non migliore)
        print("\n📝 Test 4: Aggiunta terza corsa (non migliore)")
        analysis_data_3 = {
            'viewType': 'posterior',
            'anomaly_level': 'Attenzione',
            'anomaly_score': 1.2,
            'metrics': {
                'left_knee_valgus': {'value': 9.5, 'z_score': 1.0, 'level': 'Attenzione'},
                'right_knee_valgus': {'value': 9.2, 'z_score': 0.9, 'level': 'Ottimale'},
                'pelvic_drop': {'value': 3.1, 'z_score': 1.2, 'level': 'Attenzione'},
                'cadence': {'value': 180.0, 'z_score': 0.5, 'level': 'Ottimale'},
                'knee_valgus_symmetry': {'value': 93.0, 'z_score': -0.3, 'level': 'Ottimale'}
            }
        }
        
        result = bh.update(analysis_data_3, 'run_003')
        
        assert result['run_count'] == 3, "Run count dovrebbe essere 3"
        assert result['is_new_best'] == False, "Terza corsa NON dovrebbe essere la migliore"
        assert result['best_run_id'] == 'run_002', "Best run ID dovrebbe rimanere run_002"
        
        # Verifica media incrementale con 3 valori
        expected_mean = (8.5 + 8.3 + 9.5) / 3  # 8.77
        actual_mean = bh.history_data['global_stats']['left_knee_valgus']['mean']
        assert abs(actual_mean - expected_mean) < 0.01, f"Media dovrebbe essere ~{expected_mean}, ma è {actual_mean}"
        
        print("✅ Test 4 passato: Terza corsa aggiunta, NON è la migliore")
        print(f"   Run count: {result['run_count']}")
        print(f"   Is new best: {result['is_new_best']}")
        print(f"   Media left_knee_valgus: {actual_mean:.2f}°")
        
        # Test 5: Verifica persistenza (salvataggio e caricamento)
        print("\n📝 Test 5: Verifica persistenza (salvataggio e caricamento)")
        
        # Crea nuova istanza e carica
        bh2 = BaselineHistory(history_file, ghost_folder)
        history2 = bh2.load()
        
        assert history2['run_count'] == 3, "Run count dovrebbe essere 3 dopo reload"
        assert history2['best_run_id'] == 'run_002', "Best run ID dovrebbe essere run_002 dopo reload"
        assert 'left_knee_valgus' in history2['global_stats']
        
        print("✅ Test 5 passato: Dati persistiti e ricaricati correttamente")
        
        # Test 6: get_current_baseline
        print("\n📝 Test 6: Test get_current_baseline()")
        current_baseline = bh2.get_current_baseline()
        
        assert current_baseline is not None, "Current baseline non dovrebbe essere None"
        assert current_baseline['view_type'] == 'posterior'
        assert current_baseline['n_videos'] == 3
        assert current_baseline['is_incremental'] == True
        assert 'left_knee_valgus' in current_baseline
        assert 'mean' in current_baseline['left_knee_valgus']
        
        print("✅ Test 6 passato: get_current_baseline() funziona correttamente")
        print(f"   View type: {current_baseline['view_type']}")
        print(f"   N videos: {current_baseline['n_videos']}")
        print(f"   Best run: {current_baseline['best_run_id']}")
        
        # Test 7: get_stats_summary
        print("\n📝 Test 7: Test get_stats_summary()")
        summary = bh2.get_stats_summary()
        
        assert summary['run_count'] == 3
        assert summary['best_run_id'] == 'run_002'
        assert len(summary['recent_runs']) <= 5
        
        print("✅ Test 7 passato: get_stats_summary() funziona correttamente")
        
        # Test 8: View type incompatibile
        print("\n📝 Test 8: Test view type incompatibile")
        analysis_data_lateral = {
            'viewType': 'lateral',  # Diverso da 'posterior'
            'anomaly_level': 'Ottimale',
            'metrics': {}
        }
        
        result = bh2.update(analysis_data_lateral, 'run_004')
        
        assert result['status'] == 'error', "Dovrebbe restituire errore per view type incompatibile"
        assert 'incompatibile' in result['message'].lower()
        
        print("✅ Test 8 passato: View type incompatibile gestito correttamente")
        
        # Test 9: Verifica file JSON salvato
        print("\n📝 Test 9: Verifica struttura JSON salvato")
        with open(history_file, 'r') as f:
            saved_json = json.load(f)
        
        assert 'version' in saved_json
        assert 'run_count' in saved_json
        assert 'global_stats' in saved_json
        assert 'runs_history' in saved_json
        assert saved_json['run_count'] == 3  # Non cambiato dopo errore
        
        print("✅ Test 9 passato: Struttura JSON corretta")
        print(f"   File size: {os.path.getsize(history_file)} bytes")
        
        print("\n" + "=" * 60)
        print("✅ TUTTI I TEST PASSATI!")
        print("=" * 60)
        print(f"\n📊 Summary Finale:")
        print(f"   Corse totali: {summary['run_count']}")
        print(f"   Migliore corsa: {summary['best_run_id']}")
        print(f"   Errore migliore: {summary['best_run_error']:.4f}")
        print(f"   View type: {summary['view_type']}")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FALLITO: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERRORE INATTESO: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Pulizia
        try:
            shutil.rmtree(test_dir)
            print(f"\n🧹 Directory temporanea rimossa: {test_dir}")
        except:
            pass


if __name__ == '__main__':
    success = test_baseline_history()
    sys.exit(0 if success else 1)


