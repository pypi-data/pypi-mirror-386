def split_by_md5(
    data,
    id_col='seller_id',
    exp_id='default_exp',
    test_share=0.5,
    n_test_groups=1,
    save_to_csv=False,
    output_path=None,
    salt=None,
    salt_id=None
):
    """
    Делит пользователей на контроль и несколько тестовых групп с помощью MD5-хеша, добавляя к DataFrame
    колонки test_group, exp_id и salt.

    Пример:
        test_share=0.1 и n_test_groups=2 → распределение 90% контроль, 5% test_1, 5% test_2.

    Args:
        data (str, list или pd.DataFrame): путь к CSV, список ID или DataFrame.
        id_col (str): имя колонки с ID — для CSV или DataFrame.
        exp_id (str): название эксперимента.
        test_share (float): совокупная доля всех тестовых групп.
        n_test_groups (int): количество тестовых групп.
        save_to_csv (bool): сохранять в CSV или возвращать DataFrame.
        output_path (str): путь для сохранения результата в CSV.
        salt (str или None): фиксированная соль, если нужна стабильная разбивка.
        salt_id (str или None): дополнение к соли, чтобы варьировать сессию.

    Возвращает:
        DataFrame или None: DataFrame с новыми колонками либо None при сохранении.
    """
    import pandas as pd
    import hashlib
    import os

    if salt_id is not None:
        session_salt = f"{salt}_{salt_id}" if salt else salt_id
    elif salt is not None:
        session_salt = salt
    else:
        session_salt = os.urandom(8).hex()

    print(f"Session salt: {session_salt}")

    if isinstance(data, str):
        df = pd.read_csv(data)
        if id_col not in df.columns:
            raise ValueError(f"Column {id_col} not found in CSV")
    elif isinstance(data, list):
        df = pd.DataFrame({id_col: data})
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
        if id_col not in df.columns:
            raise ValueError(f"Column {id_col} не найдена в DataFrame")
    else:
        raise TypeError("Должен быть CSV путь, список или DataFrame")

    df['exp_id'] = exp_id

    def assign_group(row):
        key = f"{row[id_col]}_{row['exp_id']}_{session_salt}".encode('utf-8')
        h = hashlib.md5(key).hexdigest()
        val = int(h, 16) / 2**128

        control_threshold = 1 - test_share

        if val < control_threshold:
            return 'control'
        else:
            segment = (val - control_threshold) / test_share
            group_idx = int(segment * n_test_groups)
            return f"test_{group_idx + 1}"

    df['test_group'] = df.apply(assign_group, axis=1)

    df['salt'] = session_salt

    if save_to_csv:
        if output_path is None:
            output_path = f"split_exp_{exp_id}.csv"
        df.to_csv(output_path, index=False)
        print(f"Результат сохранен в {output_path}")
        return None
    else:
        return df

def get_MDE(mu, std, sample_size, n_groups=2, target_share=0.5, r=1, alpha=0.05, beta=0.2):

    """
    Возвращает минимально детектируемый эффект (MDE) для пользовательской метрики при заданных параметрах теста.

    Параметры:
    mu: float
        Среднее значение метрики на исторических данных.
    std: float
        Стандартное отклонение метрики на исторических данных.
    sample_size: int
        Общий размер выборки по всем группам (контрольным и таргетным).
    n_groups: int, по умолчанию 2
        Количество групп в тесте (контроль + таргетные).
    target_share: float, по умолчанию 0.5
        Доля одной таргетной группы от всей выборки.
    r: float, по умолчанию 1
        Отношение размера самой маленькой группы к самой большой группе.
        Пример:
          - Для равных групп, например, 33% / 33% / 33%, r = 1.
          - При разбивке 50% / 25% / 25% самая маленькая группа в 2 раза меньше самой большой, 
            значит r = 0.5 (1/2).
    alpha: float, по умолчанию 0.05
        Вероятность ошибки первого рода (ложноположительная ошибка).
    beta: float, по умолчанию 0.2
        Вероятность ошибки второго рода (ложноотрицательная ошибка).

    Возвращает:
    MDE в абсолютных значениях и в процентах относительно mu.

    """
    
    from scipy import stats 
    import numpy as np
    
    t_alpha = stats.norm.ppf(1 - ((alpha / 2)), loc=0, scale=1)
    comparisons = n_groups - 1
    t_beta = stats.norm.ppf(1 - beta, loc=0, scale=1)
    sample_ratio_correction = r+2+1/r
    mde = np.sqrt(sample_ratio_correction)*(t_alpha + t_beta) * std / np.sqrt(sample_size*(1-target_share*(comparisons-1)))
    return mde, mde*100/mu

def get_bootstrap(values, n_iterations=5000, replace=True, func=None, build_plot=True, confidence_level=0.95):

    """
    Возвращает массив бутстрап-выборочных оценок заданной статистики (например, среднего).
    Опционально строит гистограмму с доверительным интервалом.

    Параметры:
    values : list или np.ndarray
        Исходные данные для бутстрапа.
    n_iterations : int, по умолчанию 5000
        Количество бутстрап-итераций.
    replace : bool, по умолчанию True
        Выборка с возвращением.
    func : callable, по умолчанию np.mean
        Вычисляемая статистика.
    build_plot : bool, по умолчанию False
        Построить гистограмму с доверительным интервалом.
    confidence_level : float, по умолчанию 0.95
        Уровень доверительного интервала (например, 0.95 для 95%).

    Возвращает:
    np.ndarray
        Массив бутстрап-значений статистики.
    """

    import numpy as np
    import matplotlib.pyplot as plt
    from tqdm import tqdm
    
    values = np.array(values)
    n = len(values)
    bootstrap_stats = np.empty(n_iterations)

    for i in tqdm(range(n_iterations)):
        sample = np.random.choice(values, size=n, replace=replace)
        bootstrap_stats[i] = func(sample)

    if build_plot:
        alpha = 1 - confidence_level
        lower_quantile = np.quantile(bootstrap_stats, alpha / 2)
        upper_quantile = np.quantile(bootstrap_stats, 1 - alpha / 2)
        median = np.median(bootstrap_stats)
        mean_ = np.mean(bootstrap_stats)

        plt.figure(figsize=(10, 6))
        plt.hist(bootstrap_stats, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(lower_quantile, color='red', linestyle='--', label=f'{100 * alpha / 2:.1f}% квантиль')
        plt.axvline(upper_quantile, color='red', linestyle='--', label=f'{100 * (1 - alpha / 2):.1f}% квантиль')
        plt.axvline(median, color='green', linestyle='-', label='Медиана')
        plt.axvline(mean_, color='black', linestyle='-', label='Среднее')
        plt.title(f'Гистограмма бутстрап-статистики с {int(confidence_level * 100)}% доверительным интервалом')
        plt.xlabel('Значение статистики')
        plt.ylabel('Частота')
        plt.legend()
        plt.grid(True)
        plt.show()

    return bootstrap_stats

def get_bootstrap_diff_mean(values_a, values_b, n_iterations=5000, replace=True, build_plot=True, confidence_level=0.95):
    """
    Рассчитывает бутстрап-распределение разницы средних двух выборок.
    Опционально строит гистограмму с доверительным интервалом.

    Параметры:
    -----------
    values_a : list или np.ndarray
        Первая выборка.
    values_b : list или np.ndarray
        Вторая выборка.
    n_iterations : int, по умолчанию 5000
        Количество итераций бутстрапа.
    replace : bool, по умолчанию True
        Семплирование с возвращением.
    build_plot : bool, по умолчанию True
        Строить ли гистограмму с доверительным интервалом.
    confidence_level : float, по умолчанию 0.95
        Уровень доверительного интервала (например, 0.95 = 95%).

    Возвращает:
    -----------
    np.ndarray
        Массив бутстрап-оценок разницы средних (values_a - values_b).
    """

    import numpy as np
    import matplotlib.pyplot as plt
    from tqdm import tqdm
    
    values_a = np.array(values_a)
    values_b = np.array(values_b)
    n_a = len(values_a)
    n_b = len(values_b)
    bootstrap_diffs = np.empty(n_iterations)

    for i in tqdm(range(n_iterations)):
        sample_a = np.random.choice(values_a, size=n_a, replace=replace)
        sample_b = np.random.choice(values_b, size=n_b, replace=replace)
        bootstrap_diffs[i] = np.mean(sample_a) - np.mean(sample_b)

    if build_plot:
        alpha = 1 - confidence_level
        lower = np.quantile(bootstrap_diffs, alpha / 2)
        upper = np.quantile(bootstrap_diffs, 1 - alpha / 2)
        median = np.median(bootstrap_diffs)
        mean_ = np.mean(bootstrap_diffs)

        plt.figure(figsize=(10, 6))
        plt.hist(bootstrap_diffs, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.axvline(lower, color='red', linestyle='--', label=f'{100 * alpha / 2:.1f}% квантиль')
        plt.axvline(upper, color='red', linestyle='--', label=f'{100 * (1 - alpha / 2):.1f}% квантиль')
        plt.axvline(median, color='green', linestyle='-', label='Медиана')
        plt.axvline(mean_, color='black', linestyle='-', label='Среднее')
        plt.title(f'Гистограмма бутстрап-разницы средних с {int(confidence_level * 100)}% дов. интервалом')
        plt.xlabel('Разница средних (values_a - values_b)')
        plt.ylabel('Частота')
        plt.legend()
        plt.grid(True)
        plt.show()

    return bootstrap_diffs


def simulate_errors(values, test_size=0.5, n_groups=2, alpha=0.05, make_plot=True, n_simulations=5000):

    """
    Эта функция замеряет ошибки первого и второго рода при тестировании метрики / среза.

    Параметры:
    values : array-like
        Исходные значения метрики.
    test_size : float, по умолчанию 0.5
        Доля тестовой группы (в долях от всей выборки).
    n_groups : int, по умолчанию 2
        Количество групп (обычно 2: контроль + тест).
    alpha : float, по умолчанию 0.05
        Уровень значимости.
    make_plot : bool, по умолчанию True
        Строить ли графики распределений ошибок.
    n_simulations : int, по умолчанию 5000
        Количество симуляций.

    Возвращает:
    fp_rate : float
        Средний уровень ошибок первого рода.
    fn_rate : float
        Средний уровень ошибок второго рода.
    mde_value : float
        Расчитанный минимально допустимый эффект.
    """
    
    import numpy as np
    from scipy import stats
    from tqdm import tqdm
    import matplotlib.pyplot as plt

    values = np.array(values)
    n_total = len(values)
    control_size = 1 - test_size

    n_control = int(n_total * control_size)
    n_test = int(n_total * test_size)

    r = test_size / control_size
    mde_value, _ = get_MDE(np.mean(values), np.std(values), n_total, n_groups=n_groups, r=r)

    false_positive_tt = []
    true_positive_tt = []

    for _ in tqdm(range(n_simulations)):
        shuffled_indices = np.random.permutation(n_total)
        idx_control = shuffled_indices[:n_control]
        idx_test = shuffled_indices[n_control : n_control + n_test]
        data_control = values[idx_control]
        data_test_no_effect = values[idx_test]
        data_test = values[idx_test] + mde_value
        pvalue_null_tt = stats.ttest_ind(data_control, data_test_no_effect, equal_var=False)[1]
        pvalue_alt_tt = stats.ttest_ind(data_control, data_test, equal_var=False)[1]
        false_positive_tt.append(int(pvalue_null_tt < alpha))
        true_positive_tt.append(int(pvalue_alt_tt < alpha))

    fp_rate = np.mean(false_positive_tt)
    fn_rate = 1 - np.mean(true_positive_tt)

    if make_plot:
        plt.figure(figsize=(14, 6))
        plt.subplot(1, 2, 1)
        plt.hist(false_positive_tt, bins=2, edgecolor='black', alpha=0.7)
        plt.title(f'Распределение ошибки первого рода. Среднее: {fp_rate:.3f}')
        plt.xlabel('Ошибка первого рода')
        plt.ylabel('Частота')
        plt.subplot(1, 2, 2)
        plt.hist(true_positive_tt, bins=2, edgecolor='black', alpha=0.7)
        plt.title(f'Распределение ошибки второго рода. Среднее (1 - мощность): {fn_rate:.3f}')
        plt.xlabel('Ошибки второго рода')
        plt.ylabel('Частота')
        plt.tight_layout()
        plt.show()

    return fp_rate, fn_rate, mde_value

def get_cuped_metrics(post_period_metric, pre_period_metric, make_plot=True):
    
    """
    Рассчитывает метрики с коррекцией CUPED для уменьшения дисперсии и улучшения оценки эффекта.

    Параметры:
    -----------
    post_period_metric : array-like
        Значения метрики в постпериоде (экспериментальный период).
    pre_period_metric : array-like
        Значения метрики в предпериоде (до эксперимента), используемые для коррекции.
    make_plot : bool, по умолчанию True
        Если True, строится гистограмма распределения исходной и CUPED метрик.
        Для построения графика применяется фильтрация выбросов: учитываются значения между 1% и 99% квантилями.

    Возвращает:
    -----------
    np.ndarray
        Скорректированные CUPED метрики, того же размера что и входные.

    Описание:
    ----------
    Функция реализует метод CUPED (Controlled-experiment Using Pre-Experiment Data),
    который снижает дисперсию итоговой метрики, используя информацию предпериода.
    Коэффициент theta вычисляется как ковариация постпериодных и предпериодных метрик (на всей выборке),
    делённая на дисперсию предпериодных метрик.
    Затем из постпериодных метрик вычитается theta, умноженное на сдвиг предпериодных метрик
    от их среднего значения.
    Для графика применяется фильтрация выбросов по 1 и 99 процентилю, чтобы улучшить визуализацию.

    Пример использования:
    ---------------------
    >>> post = np.array([10, 12, 11, 13, 12])
    >>> pre = np.array([9, 11, 10, 10, 11])
    >>> corrected = get_cuped_metrics(post, pre)
    """

    import numpy as np
    import matplotlib.pyplot as plt

    post_period_metric = np.array(post_period_metric)
    pre_period_metric = np.array(pre_period_metric)

    cov = np.cov(post_period_metric, pre_period_metric)[0, 1]
    var_pre = np.var(pre_period_metric)
    theta = cov / var_pre

    cuped_metric = post_period_metric - theta * (pre_period_metric - np.mean(pre_period_metric))

    print('theta: ', np.round(theta, 3))
    print('Среднее CUPED:', np.round(np.mean(cuped_metric), 3))
    print('Среднее метрики:', np.round(np.mean(post_period_metric), 3))
    print('Сокращение дисперсии в ', np.round(np.var(post_period_metric) / np.var(cuped_metric), 2), ' раз')

    if make_plot:
        lower_bound = np.quantile(post_period_metric, 0.01)
        upper_bound = np.quantile(post_period_metric, 0.99)
        filtered_post = post_period_metric[(post_period_metric >= lower_bound) & (post_period_metric <= upper_bound)]
        
        lower_bound_cuped = np.quantile(cuped_metric, 0.01)
        upper_bound_cuped = np.quantile(cuped_metric, 0.99)
        filtered_cuped = cuped_metric[(cuped_metric >= lower_bound_cuped) & (cuped_metric <= upper_bound_cuped)]

        plt.figure(figsize=(10, 6))
        plt.hist(filtered_post, bins=40, alpha=0.5, label='Исходная метрика', color='blue', edgecolor='black')
        plt.hist(filtered_cuped, bins=40, alpha=0.5, label='CUPED метрика', color='orange', edgecolor='black')
        plt.title('Распределение исходной и CUPED метрик\n(с удалением выбросов 1%-99% квантилей)')
        plt.xlabel('Значение метрики')
        plt.ylabel('Частота')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.show()

    return cuped_metric

def check_delta_method_ratio(num_a, den_a, num_b, den_b):
    
    """
    Проверка гипотезы о разнице долей или средних с помощью дельта-метода.

    Параметры:
    -----------
    num_a : array-like
        Числитель для группы A (например, суммы событий на пользователя).
    den_a : array-like
        Знаменатель для группы A (например, количество взаимодействий).
    num_b : array-like
        Числитель для группы B.
    den_b : array-like
        Знаменатель для группы B.

    Возвращает:
    -----------
    pvalue : float
        Двусторонний p-value на проверку равенства метрик между группами.

    Описание:
    -----------
    Рассчитывается оценка метрик как сумма числителя / сумма знаменателя для каждой группы,
    затем дисперсия метрики оценивается через дельта-метод с учетом дисперсий и ковариаций числителя и знаменателя.
    После чего считается z-статистика и p-value.

    Пример:
    --------
    >>> pval = check_delta_method_ratio(num_a, den_a, num_b, den_b)
    """

    import numpy as np
    from scipy import stats

    num_a = np.array(num_a)
    den_a = np.array(den_a)
    num_b = np.array(num_b)
    den_b = np.array(den_b)

    n_a = len(num_a)
    n_b = len(num_b)

    def estimate_metric_variance(num, den, n):
        mean_num = np.mean(num)
        mean_den = np.mean(den)
        var_num = np.var(num, ddof=1)
        var_den = np.var(den, ddof=1)
        cov_nd = np.cov(num, den, ddof=1)[0,1]

        point_estimate = np.sum(num) / np.sum(den)
        var_metric = (
            var_num / (mean_den ** 2)
            - 2 * (mean_num / (mean_den ** 3)) * cov_nd
            + (mean_num ** 2 / (mean_den ** 4)) * var_den
        ) / n
        return point_estimate, var_metric

    pe_a, var_a = estimate_metric_variance(num_a, den_a, n_a)
    pe_b, var_b = estimate_metric_variance(num_b, den_b, n_b)

    var_total = var_a + var_b
    diff = pe_b - pe_a

    z_stat = diff / np.sqrt(var_total)
    pvalue = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    return pvalue

def check_linearization_ratio(num_a, den_a, num_b, den_b):
    """
    Проверка гипотезы о разнице Ratio-метрик с использованием линеаризации (перевод метрики в поюзерную).

    Параметры:
    -----------
    num_a : array-like
        Числитель для группы A (например, суммы событий на пользователя).
    den_a : array-like
        Знаменатель для группы A (например, количество взаимодействий или показов).
    num_b : array-like
        Числитель для группы B.
    den_b : array-like
        Знаменатель для группы B.

    Возвращает:
    -----------
    pvalue : float
        Двусторонний p-value на проверку равенства линейризованных метрик между группами.
    lin_a : float
        Линеаризированная метрика для контроля
    lin_b : float
        Линеаризированная метрика для теста

    Описание:
    ----------
    Метод линеаризации (linearization) аппроксимирует отношение двух случайных величин через разложение Тейлора,
    преобразуя задачу к сравнению средних. Это снижает смещение и делает тест более стабильным для ratio-метрик.

    Пример:
    --------
    >>> pval = check_linearization_ratio(num_a, den_a, num_b, den_b)
    """

    import numpy as np
    from scipy import stats

    num_a = np.array(num_a)
    den_a = np.array(den_a)
    num_b = np.array(num_b)
    den_b = np.array(den_b)

    ratio_a = np.sum(num_a) / np.sum(den_a)

    lin_a = num_a - ratio_a * den_a
    lin_b = num_b - ratio_a * den_b

    mean_lin_a = np.mean(lin_a)
    mean_lin_b = np.mean(lin_b)

    var_lin_a = np.var(lin_a) / len(lin_a)
    var_lin_b = np.var(lin_b) / len(lin_b)

    diff = mean_lin_b - mean_lin_a

    var_total = var_lin_a + var_lin_b
    z_stat = diff / np.sqrt(var_total)
    pvalue = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    return pvalue, lin_a, lin_b


def get_poststratified_metrics(post_period_metric, stratification_feature, make_plot=True):
    """
    Рассчитывает метрики с постстратификацией для уменьшения смещения и дисперсии путем корректировки
    по стратификационным характеристикам (например, размер пользователя, регион, активность и пр.).

    Параметры:
    -----------
    post_period_metric : array-like
        Значения метрики в постпериоде (экспериментальный период).
    stratification_feature : array-like
        Категориальная или числовая характеристика, по которой выполняется стратификация.
    make_plot : bool, по умолчанию True
        Если True, строится гистограмма распределения исходной и постстратифицированной метрик.

    Возвращает:
    -----------
    np.ndarray
        Постстратифицированные метрики, скорректированные с учётом долей по стратам.
    """

    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd

    df = pd.DataFrame({
        'metric': post_period_metric,
        'strata': stratification_feature
    })

    group_means = df.groupby('strata')['metric'].mean()
    group_weights = df['strata'].value_counts(normalize=True)

    df['poststratified_metric'] = df['strata'].map(group_means * group_weights)

    print('Среднее постстратифицированной метрики:', np.round(df['poststratified_metric'].mean(), 3))
    print('Среднее исходной метрики:', np.round(df['metric'].mean(), 3))
    print('Сокращение дисперсии в ', np.round(np.var(df['metric']) / np.var(df['poststratified_metric']), 2), ' раз')

    if make_plot:
        lower_bound = np.quantile(df['metric'], 0.01)
        upper_bound = np.quantile(df['metric'], 0.99)
        filtered_original = df['metric'][(df['metric'] >= lower_bound) & (df['metric'] <= upper_bound)]

        lower_bound_post = np.quantile(df['poststratified_metric'], 0.01)
        upper_bound_post = np.quantile(df['poststratified_metric'], 0.99)
        filtered_post = df['poststratified_metric'][(df['poststratified_metric'] >= lower_bound_post) & (df['poststratified_metric'] <= upper_bound_post)]

        plt.figure(figsize=(10, 6))
        plt.hist(filtered_original, bins=40, alpha=0.5, label='Исходная метрика', color='blue', edgecolor='black')
        plt.hist(filtered_post, bins=40, alpha=0.5, label='Постстратифицированная метрика', color='orange', edgecolor='black')
        plt.title('Распределение исходной и постстратифицированной метрик\n(с удалением выбросов 1%-99% квантилей)')
        plt.xlabel('Значение метрики')
        plt.ylabel('Частота')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.show()

    return df['poststratified_metric'].values

def check_srm(group_labels, expected_split=None):
    """
    Проверка SRM (Sample Ratio Mismatch) — значимого расхождения между фактическим и ожидаемым распределением по группам.

    Параметры:
    -----------
    group_labels : array-like
        Массив с принадлежностью наблюдений к группам (например, ['A', 'A', 'B', 'A', 'B']).
    expected_split : dict, optional
        Ожидаемое распределение между группами, например {'A': 0.5, 'B': 0.5}. 
        Если None, то предполагается равный сплит.

    Возвращает:
    -----------
    pvalue : float
        p-value критерия хи-квадрат для проверки равенства распределений.

    Пример:
    --------
    >>> labels = np.random.choice(['A', 'B'], size=1000, p=[0.48, 0.52])
    >>> pval = check_srm(labels, expected_split={'A': 0.5, 'B': 0.5})
    """

    import numpy as np
    import pandas as pd
    from scipy.stats import chisquare

    group_labels = np.array(group_labels)
    group_counts = pd.Series(group_labels).value_counts().sort_index()

    if expected_split is None:
        expected_split = {g: 1 / len(group_counts) for g in group_counts.index}

    total = len(group_labels)
    expected_counts = np.array([expected_split[g] * total for g in group_counts.index])

    chi_stat, pvalue = chisquare(f_obs=group_counts.values, f_exp=expected_counts)

    print('Наблюдаемые доли:')
    for g in group_counts.index:
        print(f"  {g}: {group_counts[g] / total:.4f}")

    print('\nОжидаемые доли:')
    for g, p in expected_split.items():
        print(f"  {g}: {p:.4f}")

    print(f"\nХи-квадрат статистика: {chi_stat:.3f}")
    print(f"p-value: {pvalue:.6f}")

    if pvalue < 0.05:
        print('Обнаружено значимое расхождение (SRM detected)')
    else:
        print('Расхождение незначимо (сплит корректен)')

    return pvalue
