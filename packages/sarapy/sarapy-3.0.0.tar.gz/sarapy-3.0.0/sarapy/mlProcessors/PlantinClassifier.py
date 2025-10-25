###Documentación en https://github.com/lucasbaldezzari/sarapy/blob/main/docs/Docs.md
import logging
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sarapy.mlProcessors import PlantinFMCreator
import pickle

class PlantinClassifier(BaseEstimator, TransformerMixin):
    """Clase para implementar el pipeline de procesamiento de datos para la clasificación del tipo de operación para plantines."""
    
    def __init__(self, classifier_file = ""):
        """Constructor de la clase PlantinClassifier.
        
        Args:
            - classifier_file: String con el nombre del archivo que contiene el clasificador entrenado. El archivo a cargar es un archivo .pkl.
        """

        self.logger = logging.getLogger("PlantinClassifier")

        self.classifications_probas = None
        self.clasificaciones = None

        #cargo el clasificador con pickle. Usamos try para capturar el error FileNotFoundError
        try:
            with open(classifier_file, 'rb') as file:
                self._pipeline = pickle.load(file)
            self.logger.info("Clasificador cargado con éxito.")
        except FileNotFoundError:
            self.logger.error("El archivo no se encuentra en el directorio actual.")
            raise

    def classify(self, feature_matrix, dst_pt, inest_pt,
                 proba_threshold = 0.45, use_proba_ma = False, proba_ma_window = 10,
                update_samePlace:bool = True, update_dstpt: bool = True,
                umbral_proba_dstpt = 0.5, umbral_bajo_dstpt = 1.5,
                use_ma = True, dstpt_ma_window = 62,
                use_min_dstpt = False, factor = 0.1, **kwargs):
        """Genera la clasificación de las operaciones para plantines.
        
        - feature_matrix: Es un array con los datos (strings) provenientes de la base de datos histórica.
        La forma de newData debe ser (n,3). Las columnas de newData deben ser,
                - 1: deltaO
                - 2: ratio_dCdP
                - 3: distancias
        - dst_pt: Array con las distorsiones de plantín.
        - inest_pt: Array con flag de inestabilidad de plantín.

        kwargs: Diccionario con los argumentos necesarios para la clasificación.

        NOTA: Estas características son necesarias en base a la última versión del modelo de clasificación.
        """

        if use_ma:
            if dst_pt.shape[0] < dstpt_ma_window:
                self.logger.warning("El tamaño de la serie temporal es menor que la ventana de media móvil. No se aplicará media móvil.")
                dst_pt = self.get_dstpt_MA(dst_pt, window_size=dst_pt.shape[0], mode='same')             
            else:
                dst_pt = self.get_dstpt_MA(dst_pt, window_size=dstpt_ma_window, mode='same')

        self.clasificaciones = self._pipeline.predict(feature_matrix)
        self.classifications_probas = self._pipeline.predict_proba(feature_matrix)

        if use_proba_ma:
            if proba_ma_window >= self.classifications_probas.shape[0]:
                self.logger.warning("El tamaño de la serie temporal es menor que la ventana de media móvil. No se aplicará media móvil a las probabilidades.")
                probas_ma = self.get_probas_MA(self.classifications_probas, window_size=self.classifications_probas.shape[0], mode='same')
            else:
                probas_ma = self.get_probas_MA(self.classifications_probas, window_size=proba_ma_window, mode='same')
            self.clasificaciones[probas_ma[:,1] < proba_threshold] = 0
        else:
            # self.clasificaciones = self._pipeline.classes_[np.argmax(self.classifications_probas, axis=1)]
            self.clasificaciones[self.classifications_probas[:,1] < proba_threshold] = 0

        if update_samePlace:
            self.grouped_ops = self.groupOpsSamePlace(feature_matrix, **kwargs)
            self.clasificaciones = self.updateLabelsSamePlace(self.clasificaciones, self.grouped_ops)

        if update_dstpt:
            self.clasificaciones = self.updateLabelsFromDSTPT(self.clasificaciones, dst_pt, inest_pt,
                                                             umbral_bajo_dstpt, umbral_proba_dstpt,
                                                             use_min_dstpt, factor)

        return self.clasificaciones, self.classifications_probas

    def groupOpsSamePlace(self, X, useRatioStats = False, std_weight=1, useDistancesStats = False,
                          ratio_dcdp_umbral=0.1, dist_umbral=0.5):
        """
        Función que agrupa las operaciones que se realizaron en el mismo lugar o que sean de limpieza.
        Se entiende por operación en el mismo lugar aquellas operaciones que tengan distancias entre sí menores a 0.5.
        La función tomará las operaciones que tengan distancias menores a 0.5 y la operación anterior, dado que se supone que la 
        operación anterior se corresponde a un nuevo sitio de plantado.

        Las operaciones de limpieza son aquellas que tienen un ratio_dCdP menor a 0.3

        Args:
        - X: Array con las features de operaciones. Las columnas son deltaO, ratio_dCdP y distances.
        - useRatioStats: Booleano para usar o no las estadísticas. Por defecto es True.
        - std_weight: Peso para la desviación estándar. Por defecto es 1.
        - ratio_dcdp_umbral: Umbral para el ratio_dCdP. Por defecto es 0.1.
        - dist_umbral: Umbral para la distancia (en metros). Por defecto es 0.5.
        
        Retorna:
        - Una lista con los índices de las operaciones agrupadas.
        """

        if useRatioStats:
            median_ratio_dcdp = np.median(X[:,1])
            std_ratio_dcdp = np.std(X[:,1])
            ratio_dcdp_umbral = median_ratio_dcdp - std_weight*std_ratio_dcdp

        if useDistancesStats:
            median_dist = np.median(X[:,2])
            # std_dist = np.std(X[:,2])
            dist_umbral = median_dist #- std_weight*std_dist

        ##recorro las operaciones y comparo la actual con la siguiente. Si la distancia es menor a 0.5, la agrupo.
        ##Si el ratio_dCdP es menor a 0.3, la agrupo.
        grouped_ops = []
        distancias = X[:,2]
        ratio_dcdp = X[:,1]
        flag_cleaning = True
        for i in range(1,X.shape[0]):
            if flag_cleaning:
                sub_group = []
            if distancias[i] < dist_umbral and ratio_dcdp[i] < ratio_dcdp_umbral:
                flag_cleaning = False
                sub_group.append(i-1)
                sub_group.append(i)
            else:
                flag_cleaning = True
                if len(sub_group) > 0:
                    grouped_ops.append(sub_group)

        ##recorro grouped_ops y elimino los elementos que se repiten dentro de cada subgrupo y ordeno los indices dentro de cada subgrupo
        for i in range(len(grouped_ops)):
            grouped_ops[i] = list(set(grouped_ops[i]))
            grouped_ops[i].sort()

        return grouped_ops

    def updateLabelsSamePlace(self, labels, ops_grouped):
        """
        Función para actualizar las etiquetas de las operaciones agrupadas en el mismo lugar.

        Args:
        - labels: Array con las etiquetas de las operaciones.
        - indexes: Array con los índices correspondientes a operaciones repetidas
        """
        new_labels = labels.copy()
        for indexes in ops_grouped:
            new_labels[indexes[0]] = 1
            new_labels[indexes[1:]] = 0

        return new_labels

    def updateLabelsFromDSTPT(self, labels, dst_pt, inest_pt,
                              umbral_bajo_dstpt = 4, umbral_proba_dstpt = 0.5,
                              use_min_dstpt = False, factor = 0.1):
        """
        Función para actualizar las etiquetas de las operaciones que tengan distorsiones de plantín.
        """
        new_labels = labels.copy()

        umbral_bajo_dstpt = min(dst_pt)*(1+factor) if use_min_dstpt else umbral_bajo_dstpt
        
        ##filtro
        new_labels[(dst_pt < umbral_bajo_dstpt) & (inest_pt == 0)] = 0

        ##si inest_pt 1 es y las probs son menores a umbral_proba_dstpt, entonces la operación es 0
        new_labels[(inest_pt == 1) & (self.classifications_probas[:,1] < umbral_proba_dstpt)] = 0

        return new_labels

    def get_dstpt_MA(self, dst_pt, window_size=104, mode='same'):
        """
        Función para calcular la media móvil de una serie temporal.
        data: numpy array con los datos de la serie temporal
        window_size: tamaño de la ventana para calcular la media móvil
        """
        # return np.convolve(dst_pt, np.ones(window_size)/window_size, mode=mode)
        padding_start = dst_pt[0:window_size]
        padding_end = dst_pt[-window_size:]
        padded_data = np.concatenate([padding_start, dst_pt, padding_end])
        ma_full = np.convolve(padded_data, np.ones(window_size)/window_size, mode='same')
        return ma_full[window_size: -window_size]
    
    def get_probas_MA(self, probas, window_size=104, mode='same'):
        """
        Función para calcular la media móvil de una serie temporal.
        data: numpy array con los datos de la serie temporal
        window_size: tamaño de la ventana para calcular la media móvil
        """
        # return np.convolve(dst_pt, np.ones(window_size)/window_size, mode=mode)
        padding_start = probas[0:window_size, :]
        padding_end = probas[-window_size:, :]
        padded_data = np.vstack([padding_start, probas, padding_end])
        ma_full = np.apply_along_axis(lambda m: np.convolve(m, np.ones(window_size)/window_size, mode='same'), axis=0, arr=padded_data)
        return ma_full[window_size: -window_size, :]
    
if __name__ == "__main__":
    import os
    import pandas as pd
    import numpy as np
    from sarapy.preprocessing import TransformInputData
    from sarapy.mlProcessors import PlantinFMCreator
    from sarapy.mlProcessors import PlantinClassifier
    import json


    ## argumentos de PlantinFMCreator
    kwargs_fmcreator = {"imputeDistances":True, "distanciaMedia":1.8, "umbral_precision":0.3,
                        "dist_mismo_lugar":0.2, "max_dist":100,
                        "umbral_ratio_dCdP":2, "deltaO_medio":4,
                        "impute_ratiodcdp": True, "umbral_impute_ratiodcdp": -0.5,
                        "deltaO_ma": True, "deltaO_ma_window": 26}
            
            
    ##argumentos del método PlantinClassifier.clasiffy()
    kwargs_classifier = {"proba_threshold":0.45,
                         "use_proba_ma":False,
                         "proba_ma_window":10,
                         "update_samePlace":True,
                         "update_dstpt":True,
                         "umbral_proba_dstpt":0.5,
                         "umbral_bajo_dstpt":1.5,
                         "use_ma":True,
                         "dstpt_ma_window":62,
                         "use_min_dstpt":False,
                         "factor":0.1,
                         
                         "useRatioStats":False,
                         "std_weight":1.,
                         "useDistancesStats":False,
                         "ratio_dcdp_umbral":0.1,
                         "dist_umbral":0.5,
                         }

    historical_data_path = "examples\\2025-09-04\\UPM042N\\historical-data.json"
    with open(historical_data_path, 'r') as file:
        samples = json.load(file)

    fmcreator = PlantinFMCreator(**kwargs_fmcreator)
    tindata = TransformInputData()
    raw_X = tindata.transform(samples)

    X, dst_pt, inest_pt = fmcreator.fit_transform(raw_X)

    rf_clf_wu = PlantinClassifier(classifier_file='modelos\\pipeline_rf.pkl')

    clasificaciones, probas = rf_clf_wu.classify(X, dst_pt, inest_pt, **kwargs_classifier)
    print("media de clasificaciones", clasificaciones.mean())
    print("media de probabilidades", probas.mean(axis=0), probas.std(axis=0), np.median(probas, axis=0))
    print("primeras clasificaciones", clasificaciones[100:105])
    print("primeras probabilidades", probas[100:105])
    print("primeras distorsiones", dst_pt[100:105])
    print("primeras inestabilidades", inest_pt[100:105])
