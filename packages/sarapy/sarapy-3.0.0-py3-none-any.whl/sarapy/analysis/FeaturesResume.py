import logging
logger = logging.getLogger(__name__)  # ← "sarapy.stats"
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING) 
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.gridspec as gridspec
from matplotlib.ticker import ScalarFormatter
import seaborn as sns
from sarapy.mlProcessors import PlantinClassifier
from sarapy.preprocessing import TransformInputData
from sarapy.mlProcessors import PlantinFMCreator
from sarapy.stats import *
from sarapy.dataProcessing import OpsProcessor
import re
from datetime import datetime, time

class FeaturesResume():
    def __init__(self, raw_data, info="", filtrar=None, updateTagSeedling=False, outliers=None,
                 kwargs_fmcreator=None, kwargs_classifier=None, timeFilter=None, window_size_ma=104):
        """
        Constructor para inicializar la clase FeaturesResume.
        
        Args:
            - info (str): Información de nodo o nodos, fecha, entre otras que puedan ser de interés.
        """
        self.raw_data = raw_data
        self.updateTagSeedling = updateTagSeedling
        self.filtrar = filtrar
        self.timeFilter = timeFilter
        self.outliers = outliers
        self.window_size_ma = window_size_ma

        self.info = info
        if not kwargs_fmcreator:
            self.kwargs_fmcreator = {"imputeDistances":True, "distanciaMedia":1.8, "umbral_precision":0.3,
                                     "dist_mismo_lugar":0.2, "max_dist":100,
                                     "umbral_ratio_dCdP":2, "deltaO_medio":4,
                                     "impute_ratiodcdp": True, "umbral_impute_ratiodcdp": -0.8,
                                     "deltaO_ma": True, "deltaO_ma_window": 26}
        else:
            self.kwargs_fmcreator = kwargs_fmcreator
            
        if not kwargs_classifier:
            self.kwargs_classifier = {"proba_threshold":0.2,
                                      "use_proba_ma":False,
                                      "proba_ma_window":10,
                                      "update_samePlace":True,
                                      "update_dstpt":True,
                                      "useRatioStats":False,
                                      "std_weight":1.,
                                      "useDistancesStats":False,
                                      "ratio_dcdp_umbral":0.0,
                                      "dist_umbral":0.5,
                                      "umbral_bajo_dstpt":4,
                                      "umbral_proba_dstpt":0.70,
                                      "use_ma":True,
                                      "dstpt_ma_window":104,
                                      "use_min_dstpt":False,
                                      "factor":0.1}
        else:
            self.kwargs_classifier = kwargs_classifier

        if timeFilter:
            self.raw_data = self.filter_raw_by_time_window(**timeFilter)
            
        self.plantinFMCreator = PlantinFMCreator(**self.kwargs_fmcreator)
        self.tid = TransformInputData()
        self.data = self.transformRawData(self.raw_data)
        
        if self.filtrar == 1:
            self.data = self.data[self.data["tag_seedling"] == 1]
        elif self.filtrar == 0:
            self.data = self.data[self.data["tag_seedling"] == 0]

        if "dst_pt" in self.data.columns:
            if len(self.data["dst_pt"]) < window_size_ma:
                self.data["dst_pt_ma"] = self.getSensorMA(window_size=len(self.data["dst_pt"]))
            else:
                self.data["dst_pt_ma"] = self.getSensorMA(window_size=window_size_ma)

        if "tag_seed_probas1" in self.data.columns:
            if len(self.data["tag_seed_probas1"]) < window_size_ma:
                self.data["tag_seed_probas1_ma"] = self.getProbasMA(window_size=len(self.data["tag_seed_probas1"]))
            else:
                self.data["tag_seed_probas1_ma"] = self.getProbasMA(window_size=window_size_ma)

    def transformRawData(self, raw_data):
        """
        Método para pre-procesar la información y obtener un DataFrame con las características que se usan.

        Características a tomar:
        N_MODE

        Retorna:
        DataFrame con las características siguientes:
            - nodo
            - tag_seedling
            - tag_seedling_probas
            - raw_tag_seedling
            - tag_fertilizer
            - raw_tag_fertilizer
            - deltaO
            - ratio_dCdP
            - distances
            - precision: del gps
            - dst_pt
            - inest_pt
            - latitud
            - longitud
        """
        
        samples = self.tid.transform(raw_data) #transformo los datos
        temp_rawdatadf = pd.DataFrame(raw_data)
        temp_samplesdf = pd.DataFrame(samples)
        temporal_features, dst_pt, inest_pt = self.plantinFMCreator.fit_transform(samples)
        columns = [     'nodo',
                        'tag_seedling',
                        'tag_seed_probas1',
                        'tag_seed_probas0',
                        'raw_tag_seedling',
                        'tag_fertilizer',
                        'raw_tag_fertilizer',
                        'deltaO',
                        'ratio_dCdP',
                        'time_ac',
                        'distances',
                        'precision',
                        'dst_pt',
                        'inest_pt',
                        'latitud',
                        'longitud',
                    ]

        #genero df
        data = pd.DataFrame(columns=columns)
        data["nodo"] = temp_rawdatadf["nodo"]
        tags_seed_updated, probas = self.classifiedData(**self.kwargs_classifier)
        if self.updateTagSeedling:
            data["tag_seedling"] = tags_seed_updated
        else:
            data["tag_seedling"] = temp_rawdatadf["tag_seedling"]
        data["tag_seed_probas1"] = probas[:,1]
        data["tag_seed_probas0"] = probas[:,0]
        data["raw_tag_seedling"] = temp_rawdatadf["raw_tag_seedling"]
        data["tag_fertilizer"] = temp_rawdatadf["tag_fertilizer"]
        data["raw_tag_fertilizer"] = temp_rawdatadf["raw_tag_fertilizer"]
        data["deltaO"] = temporal_features[:,0]
        data["ratio_dCdP"] = temporal_features[:,1]
        data["time_ac"] = temp_samplesdf["TIME_AC"]
        data["distances"] = temporal_features[:,2]
        data["precision"] = temp_samplesdf["precision"]
        data["dst_pt"] = dst_pt
        data["inest_pt"] = inest_pt
        data["latitud"] = temp_samplesdf["latitud"]
        data["longitud"] = temp_samplesdf["longitud"]

        if self.outliers:
            data = self.removeOutliers(data.copy(), self.outliers)

        return data

    def classifiedData(self, classifier_file = 'modelos\\pipeline_rf.pkl', **kwargs_classifier):

        raw_X = self.tid.transform(self.raw_data)
        X, dst_pt, inest_pt = self.plantinFMCreator.fit_transform(raw_X)

        # ratio_dcdp_median = np.median(X[:, 1])
        ##reemplazo los datos de X[:, 1] por la mediana si están por debajo de -10
        # X[:, 1] = np.where(X[:, 1] < -0.8, ratio_dcdp_median, X[:, 1])
        # X[:, 0] = self.getMA(X[:, 0], window_size=26)

        clasificador = PlantinClassifier(classifier_file=classifier_file)

        clasificaciones, probas = clasificador.classify(X, dst_pt, inest_pt, **kwargs_classifier)

        return clasificaciones, probas

    def removeOutliers(self, data, limits:dict={"deltaO": (0, 3600),
                                          "precision": (0, 10000)}):
        """
        Función para eliminar outliers de las características procesadas.
        """

        ##chqueo que columnas sí están dentro de self.data y limits.
        ##las que no están, se ignoran y se muestra un mensaje de warning
        ##actualizo las columnas dentro de limits eliminando las que no están en self.data

        for col in list(limits.keys()):
            if col not in data.columns:
                logger.warning(f"La columna {col} no está en los datos y será ignorada.")
                del limits[col]

        ##elimino outliers
        for col, (lower, upper) in limits.items():
            data = data[(data[col] >= lower) & (data[col] <= upper)]

        return data

    def getResume(self, to="all", pctbajo_value=1, pctalto_value=14, lista_funciones=None):
        """
        Método para obtener un resumen de las características procesadas.
        Para todas las características se obtienen los siguientes estadísticos:
        - count
        - over_total
        - media
        - mediana
        - desviación estándar (std)
        - mínimo
        - máximo
        - skew
        - kurtosis

        Además, para el caso de distorsión de plantin (dst_pt) se agrega pctbajo y pctalto.

        Se calculan para todos los datos y para tag_seedling = 1 e tag_seedling = 0

        Se retorna una pivote_table usando los indexes = ["all","1s","0s"]
        """
        if not lista_funciones:
            lista_funciones = ["count", "mean", "median","std", "min", "max", "skew", "kurt"]
        data_wo_node = self.data.copy()
        data_wo_node = data_wo_node.drop(columns=["nodo"])
        num_cols = data_wo_node.select_dtypes(include="number").columns

        if to == 1:
            data_wo_node = data_wo_node[data_wo_node["tag_seedling"] == 1]
        elif to == 0:
            data_wo_node = data_wo_node[data_wo_node["tag_seedling"] == 0]

        stats = data_wo_node[num_cols].agg(lista_funciones)

        operaciones = len(self.data)
        over_val = (len(data_wo_node) / operaciones) if operaciones > 0 else np.nan
        over = pd.Series(over_val, index=stats.columns, name="over_total")

        arriba = stats.loc[["count"]]
        abajo  = stats.drop(index=["count"])
        stats  = pd.concat([arriba, over.to_frame().T, abajo], axis=0)

        if "dst_pt" in data_wo_node.columns:
            pct_bajo = float(np.mean(data_wo_node["dst_pt"] < pctbajo_value))
            pct_alto = float(np.mean(data_wo_node["dst_pt"] > pctalto_value))
            # Insertamos/actualizamos esas filas en la columna dst_pt.
            stats.loc["pct_bajo", "dst_pt"] = pct_bajo
            stats.loc["pct_alto", "dst_pt"] = pct_alto

        ##reemplazo los valores NaN por "no aplica"
        stats = stats.fillna("not apply")

        return stats
    
    def getSensorMA(self, window_size=104, mode='same'):
        """
        Función para calcular la media móvil de una serie temporal.
        data: numpy array con los datos de la serie temporal
        window_size: tamaño de la ventana para calcular la media móvil
        """
        # return np.convolve(self.data["dst_pt"].values, np.ones(window_size)/window_size, mode=mode)
        ##para evitar ceros al inicio y al final debido a la convolución, agrego padding
        ##pongo los primeros window_size valores de la señal al inicio y los últimos window_size valores al final
        padding_start = self.data["dst_pt"].values[0:window_size]
        padding_end = self.data["dst_pt"].values[-window_size:]
        padded_data = np.concatenate([padding_start, self.data["dst_pt"].values, padding_end])
        ma_full = np.convolve(padded_data, np.ones(window_size)/window_size, mode='same')
        return ma_full[window_size: -window_size]
    
    def getProbasMA(self, window_size=104, mode='same'):
        """
        Función para calcular la media móvil de una serie temporal.
        data: numpy array con los datos de la serie temporal
        window_size: tamaño de la ventana para calcular la media móvil
        """
        ##para evitar ceros al inicio y al final debido a la convolución, agrego padding
        ##copio los primeros y últimos valores usando la misma cantidad que window_size
        ##pongo los primeros window_size valores de la señal al inicio y los últimos window_size valores al final
        padding_start = self.data["tag_seed_probas1"].values[0:window_size]
        padding_end = self.data["tag_seed_probas1"].values[-window_size:]
        padded_data = np.concatenate([padding_start, self.data["tag_seed_probas1"].values, padding_end])
        ma_full = np.convolve(padded_data, np.ones(window_size)/window_size, mode='same')
        return ma_full[window_size: -window_size]
    
    def getMA(self, data: np.array, window_size=104, mode='same'):
        """
        Función para calcular la media móvil de una serie temporal.
        data: numpy array con los datos de la serie temporal
        window_size: tamaño de la ventana para calcular la media móvil
        """
        ##para evitar ceros al inicio y al final debido a la convolución, agrego padding
        ##copio los primeros y últimos valores usando la misma cantidad que window_size
        ##pongo los primeros window_size valores de la señal al inicio y los últimos window_size valores al final
        padding_start = data[0:window_size]
        padding_end = data[-window_size:]
        padded_data = np.concatenate([padding_start, data, padding_end])
        ma_full = np.convolve(padded_data, np.ones(window_size)/window_size, mode='same')
        return ma_full[window_size: -window_size]

    def to_time_obj(self,t):
        """
        Acepta 'HH:MM[:SS]' 24h o 'h:MM[:SS] a.m./p.m.' (con o sin puntos/espacios) y retorna datetime.time.
        """
        if isinstance(t, time):
            return t
        s = str(t).strip().lower()
        # normalizar variantes 'a.m.', 'a. m.', etc. → 'am'/'pm'
        s = re.sub(r'\s+', '', s)            # quitar espacios
        s = s.replace('.', '')               # quitar puntos
        s = s.replace('a m', 'am').replace('p m', 'pm')  # por si quedan
        # 12h con am/pm
        if 'am' in s or 'pm' in s:
            for fmt in ('%I:%M:%S%p', '%I:%M%p'):
                try: return datetime.strptime(s.upper(), fmt).time()
                except ValueError: pass
            raise ValueError(f"No pude interpretar la hora 12h: {t!r}")
        # 24h
        for fmt in ('%H:%M:%S', '%H:%M'):
            try: return datetime.strptime(t, fmt).time()
            except ValueError: pass
        raise ValueError(f"No pude interpretar la hora 24h: {t!r}")

    def time_to_td(self,t: time) -> pd.Timedelta:
        return pd.Timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)

    def filter_raw_by_time_window(self,
                                  start_time, end_time,
                                  tz_target: str = "America/Montevideo",
                                  timestamp_key: str = "timestamp",
                                  inclusive: str = "both",  # 'both' | 'neither' | 'left' | 'right',
                                  inplace = False):
        """
        Filtra registros cuyo 'timestamp' caiga entre [start_time, end_time] en la zona 'tz_target'.
        - start_time/end_time: 'HH:MM[:SS]' 24h o 'h:MM[:SS] a.m./p.m.' o datetime.time
        - Soporta ventanas que cruzan medianoche (p.ej. 23:30 a 01:15).
        Retorna la misma estructura: lista de dicts si raw_data era lista; DataFrame si era DataFrame.
        """
        df = pd.DataFrame(self.raw_data) if not isinstance(self.raw_data, pd.DataFrame) else self.raw_data.copy()
        if timestamp_key not in df.columns:
            raise KeyError(f"Columna {timestamp_key!r} no encontrada en los datos.")

        # 1) Parseo y conversión de zona horaria
        ts_utc = pd.to_datetime(df[timestamp_key], utc=True, errors='coerce')
        if ts_utc.isna().any():
            n_bad = int(ts_utc.isna().sum())
            raise ValueError(f"Hay {n_bad} timestamps inválidos/imposibles de parsear.")
        ts_local = ts_utc.dt.tz_convert(tz_target)

        # 2) Hora-del-día como Timedelta desde medianoche local
        tod = ts_local - ts_local.dt.normalize()

        # 3) Ventana objetivo → Timedelta
        t0 = self.time_to_td(self.to_time_obj(start_time))
        t1 = self.time_to_td(self.to_time_obj(end_time))

        # 4) Construcción de máscara (maneja cruce de medianoche)
        if t0 <= t1:
            mask = tod.between(t0, t1, inclusive=inclusive)
        else:
            # ejemplo: 23:30 → 01:15  (dos tramos)
            mask = tod.ge(t0) | tod.le(t1)
            if inclusive in ("neither", "right"):  # ajustar extremos si no inclusivo
                mask &= ~tod.eq(t0)
            if inclusive in ("neither", "left"):
                mask &= ~tod.eq(t1)

        filtered = df[mask]
        #me quedo con los indices donde se cumpla df[mask] y aplico a self.raw_data de origen

        ##chequeo que filtered no esté vacio, sino retorno None
        if filtered.empty or len(filtered) < 10:
            logger.warning("El filtro de tiempo resultó en un conjunto vacío.")
            print("El filtro de tiempo resultó en un conjunto vacío.")
            return None

        #si inplace, actualizo filtro raw_data y retorno un nuevo objeto FeaturesResume, sino retorno los datos filtrados
        if inplace:
            return filtered.to_dict(orient='records') if not isinstance(self.raw_data, pd.DataFrame) else filtered
        else:
            #copio el estado del objeto actual
            new_fr = FeaturesResume(
                raw_data = filtered.to_dict(orient='records') if not isinstance(self.raw_data, pd.DataFrame) else filtered,
                info = self.info,
                filtrar = self.filtrar,
                updateTagSeedling = self.updateTagSeedling,
                kwargs_fmcreator = self.kwargs_fmcreator,
                kwargs_classifier = self.kwargs_classifier,
                timeFilter = None,  # ya apliqué el filtro
                outliers = self.outliers,
                window_size_ma=self.window_size_ma,
            )

            return new_fr
            
    def _get_ratiodCdPPlot(self, figsize = (10,6), show = False):
        """
        Función para retornar (y graficar si se desea) un gráfico de línea de
        ratio_dCdP y tag_seedling. El eje Y izquierdo es ratio y el derecho es el tag_seedling
        """
        # Verificamos que existan las columnas necesarias
        if "ratio_dCdP" not in self.data.columns or "tag_seedling" not in self.data.columns:
            raise ValueError("Faltan columnas necesarias para graficar.")

        fig, ax1 = plt.subplots(figsize=figsize)

        # Eje izquierdo: ratio_dCdP
        ax1.plot(self.data["ratio_dCdP"], label='ratio_dCdP', color='blue')
        ax1.set_xlabel("Operación")
        ax1.set_ylabel("Ratio dCdP", color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')

        # Forzar eje Y en formato decimal
        ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
        ax1.ticklabel_format(style='plain', axis='y')  # Asegura formato decimal

        # Eje derecho: tag_seedling
        ax2 = ax1.twinx()
        ax2.plot(self.data["tag_seedling"], label='tag_seedling', color='red')
        ax2.set_ylabel("Tag Seedling", color='red')
        ax2.tick_params(axis='y', labelcolor='red')
        ax2.set_ylim(0, 5)  # Limitar el eje Y de tag_seedling entre 0 y 5

        plt.title(f"Análisis de {self.info} - Ratio dCdP y Tag Seedling")
        fig.tight_layout()

        if show:
            plt.show()

        return fig
    
    def plotFeatureComparison(
        self,
        feature1: str,
        feature2: str,
        y1limits=None,
        y2limits=None,
        figsize=(10, 6),
        title=None,
        show=False,
        save=False,
        filename=None,
        colors = ('blue', 'red'),
        *,
        line1: bool = True,        # ¿dibujar línea en ax1?
        line2: bool = True,        # ¿dibujar línea en ax2?
        marker1: str | None = None,  # p.ej. 'o', 's', '^' para ax1
        marker2: str | None = None,  # p.ej. 'o', 's', '^' para ax2
        markersize: float = 6
    ):
        """
        Genera un gráfico de comparación entre dos características en ejes y diferentes.
        Se puede elegir si cada eje usa línea, solo marcadores, o ambos.

        Args:
            - feature1, feature2: nombres de columnas en self.data.
            - y1limits, y2limits: tuplas (ymin, ymax) opcionales.
            - figsize: tamaño de la figura.
            - show: si se muestra la figura.
            - line1, line2: True = dibuja línea; False = solo marcadores (si se especifica marker).
            - marker1, marker2: símbolos de marcador (ej. 'o'); None = sin marcador.
            - markersize: tamaño del marcador.
        """

        # chequeo que las características estén en los datos
        if feature1 not in self.data.columns or feature2 not in self.data.columns:
            raise ValueError("Faltan columnas necesarias para graficar.")

        fig, ax1 = plt.subplots(figsize=figsize)

        # ---- Eje izquierdo: feature1
        ls1 = '-' if line1 else 'None'  # 'None' evita trazar línea
        ax1.plot(
            self.data.index,
            self.data[feature1].values,
            label=feature1,
            color=colors[0],
            linestyle=ls1,
            marker=marker1,
            markersize=markersize
        )
        ax1.set_xlabel("Operación")
        ax1.set_ylabel(feature1, color=colors[0])
        ax1.tick_params(axis='y', labelcolor=colors[0])

        # Formato decimal y límites opcionales
        ax1.yaxis.set_major_formatter(ScalarFormatter(useMathText=False))
        ax1.ticklabel_format(style='plain', axis='y')
        if y1limits is not None:
            ax1.set_ylim(y1limits)

        # ---- Eje derecho: feature2
        ax2 = ax1.twinx()
        ls2 = '-' if line2 else 'None'
        ax2.plot(
            self.data.index,
            self.data[feature2].values,
            label=feature2,
            color=colors[1],
            linestyle=ls2,
            marker=marker2,
            markersize=markersize
        )
        ax2.set_ylabel(feature2, color=colors[1])
        ax2.tick_params(axis='y', labelcolor=colors[1])
        if y2limits is not None:
            ax2.set_ylim(y2limits)

        # Título y layout
        if title is not None:
            plt.title(title)
        else:
            plt.title(f"Análisis de {self.info} - {feature1} y {feature2}")
        fig.tight_layout()

        # Leyenda combinada de ambos ejes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

        if save:
            if filename is not None:
                plt.savefig(filename)
            else:
                plt.savefig(f"feature_comparison_{feature1}_{feature2}.png")

        if show:
            plt.show()
        else:
            plt.close(fig)  # Cierra la figura para liberar memoria

    ##gráfico de dispersión para comparar la distribución de 0s y 1s
    def plot_geo_compare(
        self,
        feature_col: str,
        lat_col: str = "latitud",
        lon_col: str = "longitud",
        tag_col: str = "tag_seedling",
        cmap: str = "winter",
        figsize=(14, 6),
        s: float = 10.0,
        alpha: float = 0.8,
        equal_aspect: bool = True,
        save = False,
        show = True,
        filename = None,
        # ---- NUEVO: control de colorbar y límites de color ----
        vmin: float | None = None,
        vmax: float | None = None,
        cb_width: float = 0.02,   # ancho relativo del colorbar (fracción del eje del mapa)
        cb_pad: float = 0.02,     # separación entre mapa y colorbar (en fracción)
        cb_ticks: int | None = None,  # número aprox. de ticks (None = automático)
    ):
        # -------- Validación --------
        df = self.data
        required_cols = {lat_col, lon_col, tag_col, feature_col}
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas en el DataFrame: {missing}")

        # Datos y máscaras sin NaN
        left = df[[lat_col, lon_col, tag_col]].dropna()
        right = df[[lat_col, lon_col, feature_col]].dropna()

        # -------- Figura principal (2 subplots, sin colorbar aún) --------
        fig, (ax0, ax1) = plt.subplots(1, 2, figsize=figsize, constrained_layout=False)
        plt.subplots_adjust(wspace=0.25, left=0.06, right=0.94, bottom=0.10, top=0.90)

        # -------- Subplot izquierdo: binario rojo/verde --------
        color_map = {1: "green", 0: "red"}
        colors_left = left[tag_col].map(color_map).fillna("gray").values
        ax0.scatter(left[lon_col], left[lat_col], c=colors_left, s=s, alpha=alpha, linewidths=0)
        ax0.set_xlabel("Longitud"); ax0.set_ylabel("Latitud")
        ax0.set_title("Semilleros (verde=1, rojo=0)")
        from matplotlib.lines import Line2D
        leg = [
            Line2D([0],[0], marker='o', color='w', label=f"{tag_col} = 1", markerfacecolor='green', markersize=8),
            Line2D([0],[0], marker='o', color='w', label=f"{tag_col} = 0", markerfacecolor='red', markersize=8),
        ]
        if (~left[tag_col].isin([0,1])).any():
            leg.append(Line2D([0],[0], marker='o', color='w', label=f"{tag_col} ≠ 0/1", markerfacecolor='gray', markersize=8))
        ax0.legend(handles=leg, loc="best", frameon=True)

        # -------- Subplot derecho: continuo por feature con vmin/vmax --------
        vals = right[feature_col].to_numpy(dtype=float)
        # límites automáticos si no se pasan
        vmin_eff = np.nanmin(vals) if vmin is None else float(vmin)
        vmax_eff = np.nanmax(vals) if vmax is None else float(vmax)

        sc = ax1.scatter(
            right[lon_col], right[lat_col],
            c=vals, cmap=cmap, vmin=vmin_eff, vmax=vmax_eff,
            s=s, alpha=alpha, linewidths=0
        )
        ax1.set_xlabel("Longitud"); ax1.set_ylabel("Latitud")
        ax1.set_title(f"Color por feature: {feature_col}")

        # -------- Colorbar delgado adosado al segundo mapa --------
        divider = make_axes_locatable(ax1)
        # 'size' puede ser porcentaje del eje del mapa (p.ej. "2%")
        cax = divider.append_axes("right", size=f"{cb_width*100:.1f}%", pad=cb_pad)
        cbar = fig.colorbar(sc, cax=cax)
        cbar.set_label(feature_col)
        if cb_ticks is not None and cb_ticks > 0:
            cbar.locator = plt.MaxNLocator(cb_ticks)
            cbar.update_ticks()
        # Opcional: tipografía/tamaño de ticks del colorbar
        cbar.ax.tick_params(labelsize=8)

        # -------- Ajustes comunes --------
        if equal_aspect:
            ax0.set_aspect('equal', adjustable='box')
            ax1.set_aspect('equal', adjustable='box')

        # Misma caja geográfica en ambos paneles para comparación directa
        xmin = np.nanmin(df[lon_col].to_numpy())
        xmax = np.nanmax(df[lon_col].to_numpy())
        ymin = np.nanmin(df[lat_col].to_numpy())
        ymax = np.nanmax(df[lat_col].to_numpy())
        for ax in (ax0, ax1):
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)


        if save:
            if filename is not None:
                plt.savefig(filename)
            else:
                plt.savefig(f"geo_compare_{feature_col}.png")
        if show:
            plt.show()
        plt.close(fig)  # Cierra la figura para liberar memoria

if __name__ == "__main__":
    import json
    from sarapy.utils import dataMerging
    import numpy as np
    import matplotlib.pyplot as plt
    from sarapy.utils.plotting import plotTemporalData
    plt.style.use('bmh')
    
    pkg_logger = logging.getLogger("sarapy.stats")
    pkg_logger.setLevel(logging.ERROR)

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

    
    time_filter=None

    nodo = "UPM039N"
    fecha = "2025-09-04"
    save = True
    show = False

    hdpath = f"examples\\{fecha}\\{nodo}\\historical-data.json" #historical file
    pppath = f"examples\\{fecha}\\{nodo}\\post-processing-data.json" #post-processing file
    raw_data = f"examples\\{fecha}\\{nodo}\\data.json" #raw file

    with open(hdpath, 'r') as file:
        historical_data = json.load(file)
    with open(pppath, 'r') as file:
        post_data = json.load(file)
    with open(raw_data, 'r') as file:
        raw_data = json.load(file)

    merged_data = dataMerging(historical_data, post_data, raw_data, nodoName=nodo,newColumns=False, asDF=False)

    outliers = {
            "ratio_dCdP": (-5, 2),
            "deltaO": (0, 3600),
            "time_ac": (0, 100),
            "precision": (0, 5000),
            "distances": (0, 100)
            }

    fr = FeaturesResume(merged_data, info = nodo, filtrar=None, outliers=outliers,
                             kwargs_classifier=kwargs_classifier,
                             kwargs_fmcreator=kwargs_fmcreator,
                             updateTagSeedling=True, timeFilter=None,
                             window_size_ma=62)
    
    print(fr.data["tag_seedling"].value_counts(normalize=True))
    print(fr.getResume(to="all"))

    time_filter = {"start_time": "13:29:13",
                   "end_time": "13:43:19",
                   "tz_target": "America/Montevideo",
                   "timestamp_key": "timestamp",
                   "inclusive": "both",  # 'both' | 'neither' | 'left' | 'right',
                   "inplace": False
                   }
    
    new_fr = fr.filter_raw_by_time_window(**time_filter)
    print(new_fr.getResume(to="all"))
    new_fr.plotFeatureComparison("dst_pt_ma", "tag_seed_probas1", figsize=(12, 8),
                                 show=True, line2=True, marker2=None)
    new_fr.plotFeatureComparison("dst_pt_ma", "tag_seedling", figsize=(12, 8),
                                 show=True, line2=True, marker2=None)
