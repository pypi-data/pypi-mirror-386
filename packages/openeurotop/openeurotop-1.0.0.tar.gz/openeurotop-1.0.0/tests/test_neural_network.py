"""
Tests unitaires pour le module neural_network et neural_network_clash

Tests des fonctionnalités de réseaux de neurones pour la prédiction
du franchissement, y compris le modèle entraîné sur CLASH.
"""

import numpy as np
import pytest
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from openeurotop import neural_network
from openeurotop.neural_network_clash import CLASHNeuralNetwork, predict_with_clash


class TestNeuralNetworkBasic:
    """Tests pour le module neural_network de base"""
    
    def test_initialization(self):
        """Test initialisation du réseau"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        assert nn.architecture == [6, 10, 10, 1]
        assert len(nn.weights) == 3
        assert len(nn.biases) == 3
        assert nn.is_trained == False
    
    def test_custom_architecture(self):
        """Test initialisation avec architecture personnalisée"""
        arch = [5, 8, 6, 1]
        nn = neural_network.NeuralNetworkOvertoppingPredictor(architecture=arch)
        
        assert nn.architecture == arch
        assert len(nn.weights) == len(arch) - 1
    
    def test_activation_functions(self):
        """Test fonctions d'activation"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        # Sigmoid
        assert 0 < nn.sigmoid(0) < 1
        assert nn.sigmoid(-1000) < 0.01
        assert nn.sigmoid(1000) > 0.99
        
        # Tanh
        assert -1 < nn.tanh(0) < 1
        assert nn.tanh(0) == 0
    
    def test_normalize_inputs(self):
        """Test normalisation des entrées"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        Hm0, Tm_10, h, Rc = 2.5, 6.0, 5.0, 2.0
        tan_alpha, gamma_f = 0.5, 1.0
        
        x_norm = nn.normalize_inputs(Hm0, Tm_10, h, Rc, tan_alpha, gamma_f)
        
        assert isinstance(x_norm, np.ndarray)
        assert x_norm.shape == (6,)
        # Les valeurs normalisées devraient être proches de 0 pour les valeurs "moyennes"
        assert np.all(np.abs(x_norm) < 5)  # Pas trop loin de la moyenne
    
    def test_forward_pass(self):
        """Test propagation avant"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        x = np.random.randn(6)
        output = nn.forward(x)
        
        assert isinstance(output, float)
        assert not np.isnan(output)
        assert not np.isinf(output)
    
    def test_predict(self):
        """Test prédiction complète"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        result = nn.predict(
            Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, 
            alpha_deg=35.0, gamma_f=1.0
        )
        
        assert isinstance(result, dict)
        assert 'q' in result
        assert 'log_q' in result
        assert 'warning' in result
        assert 'is_trained' in result
        assert 'recommendation' in result
        
        assert result['is_trained'] == False
        assert result['q'] > 0
    
    def test_predict_various_inputs(self):
        """Test prédictions avec différents paramètres"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        # Test 1: Structure haute avec faible revanche
        r1 = nn.predict(3.0, 7.0, 15.0, 2.0, 30.0)
        
        # Test 2: Structure basse avec grande revanche
        r2 = nn.predict(1.5, 5.0, 8.0, 4.0, 45.0)
        
        assert r1['q'] > 0
        assert r2['q'] > 0
        # Les deux prédictions devraient être différentes
        assert r1['q'] != r2['q']


class TestNeuralNetworkComparison:
    """Tests pour comparaison avec formules empiriques"""
    
    def test_comparison_function(self):
        """Test fonction de comparaison"""
        result = neural_network.neural_network_comparison(
            Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, 
            alpha_deg=35.0, gamma_f=1.0
        )
        
        assert isinstance(result, dict)
        assert 'q_empirical' in result
        assert 'q_neural' in result
        assert 'method_used' in result
        assert 'recommendation' in result
        assert 'neural_warning' in result
        
        assert result['method_used'] == 'empirical'
        assert result['q_empirical'] > 0
        assert result['q_neural'] > 0
    
    def test_comparison_order_of_magnitude(self):
        """Test que les deux méthodes donnent des ordres de grandeur similaires"""
        result = neural_network.neural_network_comparison(
            Hm0=2.0, Tm_10=5.5, h=8.0, Rc=2.5, 
            alpha_deg=30.0
        )
        
        q_emp = result['q_empirical']
        q_nn = result['q_neural']
        
        # Les deux méthodes devraient donner des valeurs positives
        assert q_emp > 0
        assert q_nn > 0
        
        # Ordre de grandeur similaire (même si pas entraîné)
        # On vérifie juste qu'on n'a pas des valeurs complètement folles
        assert 1e-10 < q_emp < 1
        assert 1e-10 < q_nn < 1


class TestTrainingDataStructure:
    """Tests pour structures de données d'entraînement"""
    
    def test_training_template(self):
        """Test template de données d'entraînement"""
        template = neural_network.prepare_training_data_structure()
        
        assert isinstance(template, dict)
        assert 'description' in template
        assert 'inputs' in template
        assert 'output' in template
        assert 'data_format' in template
        assert 'preprocessing' in template
        assert 'training' in template
    
    def test_synthetic_data_generation(self):
        """Test génération de données synthétiques"""
        data = neural_network.generate_synthetic_training_example(n_samples=50)
        
        assert isinstance(data, dict)
        assert 'X' in data
        assert 'y' in data
        assert 'feature_names' in data
        assert 'n_samples' in data
        
        X = data['X']
        y = data['y']
        
        assert X.shape == (50, 6)
        assert y.shape == (50,)
        assert len(data['feature_names']) == 6
        
        # Toutes les features doivent être positives (physique)
        assert np.all(X[:, :4] > 0)  # Hm0, Tm_10, h, Rc
        assert np.all(X[:, 4] > 0)   # tan_alpha
        assert np.all(X[:, 5] > 0)   # gamma_f
    
    def test_synthetic_data_diversity(self):
        """Test diversité des données synthétiques"""
        data = neural_network.generate_synthetic_training_example(n_samples=100)
        
        X = data['X']
        
        # Vérifier la diversité (std > 0)
        for i in range(X.shape[1]):
            assert np.std(X[:, i]) > 0


class TestInfoAndDocumentation:
    """Tests pour informations et documentation"""
    
    def test_info_function(self):
        """Test fonction d'information"""
        info = neural_network.info_neural_network_usage()
        
        assert isinstance(info, str)
        assert len(info) > 100
        assert 'AVANTAGES' in info
        assert 'INCONVÉNIENTS' in info
        assert 'RECOMMANDATION' in info
        assert 'CLASH' in info


class TestCLASHNeuralNetwork:
    """Tests pour le réseau de neurones CLASH"""
    
    def test_clash_initialization(self):
        """Test initialisation du réseau CLASH"""
        model = CLASHNeuralNetwork()
        
        assert model.architecture == [10, 20, 15, 1]
        assert len(model.weights) > 0
        assert len(model.biases) > 0
        assert model.is_trained == False
    
    def test_clash_custom_architecture(self):
        """Test architecture personnalisée CLASH"""
        arch = [5, 10, 5, 1]
        model = CLASHNeuralNetwork(architecture=arch)
        
        assert model.architecture == arch
    
    def test_normalization(self):
        """Test normalisation des features"""
        model = CLASHNeuralNetwork()
        
        X = np.random.randn(100, 10)
        X_norm = model.normalize_features(X)
        
        assert X_norm.shape == X.shape
        # Après normalisation, mean ~0 et std ~1
        assert np.abs(np.mean(X_norm)) < 0.1
        assert 0.9 < np.std(X_norm) < 1.1
    
    def test_forward_propagation(self):
        """Test propagation avant CLASH"""
        model = CLASHNeuralNetwork()
        
        X = np.random.randn(50, 10)
        X_norm = model.normalize_features(X)
        
        y_pred = model.forward(X_norm)
        
        assert y_pred.shape == (50,)
        assert not np.any(np.isnan(y_pred))
        assert not np.any(np.isinf(y_pred))
    
    def test_training_small_dataset(self):
        """Test entraînement sur petit dataset"""
        model = CLASHNeuralNetwork(architecture=[5, 10, 1])
        
        # Générer données synthétiques
        X = np.random.randn(100, 5)
        y = np.random.randn(100)
        
        history = model.train(
            X, y,
            epochs=10,
            learning_rate=0.01,
            batch_size=20,
            validation_split=0.2,
            verbose=False
        )
        
        assert isinstance(history, dict)
        assert 'train_loss' in history
        assert 'val_loss' in history
        assert 'epoch' in history
        
        assert model.is_trained == True
        assert len(history['train_loss']) > 0
    
    def test_prediction_after_training(self):
        """Test prédiction après entraînement"""
        model = CLASHNeuralNetwork(architecture=[3, 5, 1])
        
        # Entraînement simple
        X = np.random.randn(50, 3)
        y = np.sum(X, axis=1)  # Simple relation linéaire
        
        model.train(X, y, epochs=50, verbose=False)
        
        # Prédiction
        X_test = np.random.randn(10, 3)
        y_pred = model.predict(X_test)
        
        assert y_pred.shape == (10,)
        assert not np.any(np.isnan(y_pred))
    
    def test_single_prediction(self):
        """Test prédiction unique (1D input)"""
        model = CLASHNeuralNetwork(architecture=[4, 5, 1])
        
        X = np.random.randn(30, 4)
        y = np.random.randn(30)
        model.train(X, y, epochs=10, verbose=False)
        
        # Prédiction 1D
        x_single = np.random.randn(4)
        y_pred = model.predict(x_single)
        
        assert isinstance(y_pred, (float, np.floating))
    
    def test_save_load_model(self):
        """Test sauvegarde et chargement du modèle"""
        import tempfile
        
        model = CLASHNeuralNetwork(architecture=[3, 5, 1])
        
        X = np.random.randn(40, 3)
        y = np.random.randn(40)
        model.train(X, y, epochs=10, verbose=False)
        
        # Prédiction avant sauvegarde
        X_test = np.array([[1, 2, 3]])
        y_pred_before = model.predict(X_test)
        
        # Sauvegarder
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            temp_path = f.name
        
        model.save_model(temp_path)
        
        # Charger dans nouveau modèle
        model2 = CLASHNeuralNetwork()
        model2.load_model(temp_path)
        
        # Prédiction après chargement
        y_pred_after = model2.predict(X_test)
        
        # Devrait être identique
        assert np.allclose(y_pred_before, y_pred_after, rtol=1e-5)
        assert model2.is_trained == True
        
        # Nettoyer
        os.remove(temp_path)


class TestCLASHTrainedModel:
    """Tests pour le modèle CLASH entraîné (si disponible)"""
    
    def test_trained_model_exists(self):
        """Vérifier si le modèle entraîné existe"""
        model_path = 'Data/clash_model.pkl'
        
        if os.path.exists(model_path):
            model = CLASHNeuralNetwork()
            model.load_model(model_path)
            
            assert model.is_trained == True
            assert 'mean' in model.scaler_params
            assert 'std' in model.scaler_params
            print(f"\n[OK] Modele CLASH charge: R2 = {model.training_info.get('final_train_loss', 'N/A')}")
        else:
            pytest.skip("Modèle CLASH non entraîné - exécuter scripts/train_clash_model.py")
    
    def test_predict_with_clash_no_model(self):
        """Test prédiction CLASH sans modèle"""
        result = predict_with_clash(
            Hm0=2.0, Tm_10=5.5, h=8.0, Rc=2.5, alpha_deg=30.0,
            model_path='nonexistent_model.pkl'
        )
        
        assert 'error' in result
        assert 'recommendation' in result
    
    @pytest.mark.skipif(not os.path.exists('Data/clash_model.pkl'),
                        reason="Modèle CLASH non entraîné")
    def test_predict_with_trained_clash(self):
        """Test prédiction avec modèle CLASH entraîné"""
        result = predict_with_clash(
            Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
        )
        
        assert 'q' in result
        assert 'log_q' in result
        assert 'is_trained' in result
        assert 'method' in result
        
        assert result['is_trained'] == True
        assert result['q'] > 0
        assert result['method'] == 'CLASH Neural Network'
    
    @pytest.mark.skipif(not os.path.exists('Data/clash_model.pkl'),
                        reason="Modèle CLASH non entraîné")
    def test_clash_various_conditions(self):
        """Test prédictions CLASH pour diverses conditions"""
        
        conditions = [
            # (Hm0, Tm_10, h, Rc, alpha_deg)
            (1.5, 5.0, 8.0, 2.0, 30.0),
            (2.5, 6.5, 10.0, 3.5, 35.0),
            (3.5, 7.5, 12.0, 1.5, 25.0),
            (1.0, 4.5, 6.0, 4.0, 40.0),
        ]
        
        for Hm0, Tm_10, h, Rc, alpha in conditions:
            result = predict_with_clash(Hm0, Tm_10, h, Rc, alpha)
            
            assert result['q'] > 0
            assert not np.isnan(result['q'])
            assert result['is_trained'] == True


class TestIntegrationWithOtherModules:
    """Tests d'intégration avec autres modules"""
    
    def test_integration_with_overtopping(self):
        """Test intégration avec module overtopping"""
        from openeurotop import overtopping
        
        # Calculer avec formules empiriques
        q_empirical = overtopping.digue_talus(
            Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
        )
        
        # Calculer avec réseau neuronal (non entraîné)
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        result_nn = nn.predict(2.5, 6.0, 10.0, 3.0, 35.0)
        
        # Les deux devraient donner des valeurs positives
        assert q_empirical > 0
        assert result_nn['q'] > 0
        
        # Et dans un ordre de grandeur raisonnable
        assert 1e-10 < q_empirical < 1
        assert 1e-10 < result_nn['q'] < 1


# Tests de performance et edge cases
class TestEdgeCases:
    """Tests des cas limites"""
    
    def test_extreme_wave_heights(self):
        """Test hauteurs de vagues extrêmes"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        # Très petite vague
        r1 = nn.predict(0.1, 3.0, 5.0, 2.0, 30.0)
        assert r1['q'] > 0
        
        # Grande vague
        r2 = nn.predict(5.0, 10.0, 15.0, 1.0, 25.0)
        assert r2['q'] > 0
    
    def test_zero_freeboard(self):
        """Test avec revanche nulle"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        result = nn.predict(2.0, 6.0, 8.0, 0.0, 30.0)
        assert result['q'] > 0
    
    def test_negative_freeboard(self):
        """Test avec revanche négative (structure submergée)"""
        nn = neural_network.NeuralNetworkOvertoppingPredictor()
        
        result = nn.predict(3.0, 7.0, 10.0, -1.0, 35.0)
        assert result['q'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

