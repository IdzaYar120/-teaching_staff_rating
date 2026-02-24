# data.py
import collections

# --- БЛОК 1 ---
# quantity - кількість (n)
# update_percentage - відсоток оновлення (% он)
# positive_feedback_percentage - відсоток позитивних відгуків (% поз)
INDICATORS_BLOCK_1 = {
    # 1.1 Навчально-методичний комплекс
    "1.1.1": {"text": "1.1.1 - робоча програма навчальної дисципліни", "weight": 10, "formula_type": "percentage_update", "variables": ["quantity", "update_percentage"], "block": 1},
    "1.1.2": {"text": "1.1.2 - ректорська контрольна робота", "weight": 5, "formula_type": "percentage_update", "variables": ["quantity", "update_percentage"], "block": 1},
    "1.1.3": {"text": "1.1.3 - конспект лекції", "weight": 20, "formula_type": "percentage_update", "variables": ["quantity", "update_percentage"], "block": 1},
    "1.1.4": {"text": "1.1.4 - методичні рекомендації до проведення практичних, семінарських, лабораторних занять", "weight": 15, "formula_type": "percentage_update", "variables": ["quantity", "update_percentage"], "block": 1},
    "1.1.5": {"text": "1.1.5 - методичні вказівки до виконання самостійної роботи", "weight": 10, "formula_type": "percentage_update", "variables": ["quantity", "update_percentage"], "block": 1},
    "1.1.6": {"text": "1.1.6 - презентації", "weight": 5, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.1.7": {"text": "1.1.7 - екзаменаційні білети", "weight": 3, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.1.8": {"text": "1.1.8 - ІНДЗ / Контрольна робота для здобувачів заочної форми навчання", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    
    # 1.2 Результати анкетування
    "1.2.1": {"text": "1.2.1 - рівня володіння матеріалом", "weight": 15, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.2": {"text": "1.2.2 - змістовності матеріалу", "weight": 15, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.3": {"text": "1.2.3 - доступності викладання матеріалу", "weight": 10, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.4": {"text": "1.2.4 - чіткості", "weight": 15, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.5": {"text": "1.2.5 - використання інноваційних методів навчання", "weight": 15, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.6": {"text": "1.2.6 - доброзичливості викладача", "weight": 10, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.7": {"text": "1.2.7 - тактовності викладача", "weight": 10, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    "1.2.8": {"text": "1.2.8 - пунктуальності викладача", "weight": 10, "formula_type": "positive_feedback", "variables": ["quantity", "positive_feedback_percentage"], "block": 1},
    
    # 1.3 Підвищення педагогічної майстерності
    "1.3.1.1": {"text": "1.3.1.1 - проведення відкритої загальноуніверситетської лекції", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.1.2": {"text": "1.3.1.2 - кафедрального лекційного, практичного (семінарського, лабораторного) заняття", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.2": {"text": "1.3.2 - взаємовідвідування занять викладачами кафедри", "weight": 2, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.3.1": {"text": "1.3.3.1 - участь в тренінгах, семінарах... в якості тренера, тьютора тощо", "weight": 15, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.3.2": {"text": "1.3.3.2 - участь в тренінгах, семінарах... в якості слухача", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.4": {"text": "1.3.4 - керівництво стажуванням викладача іншого закладу", "weight": 5, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.5": {"text": "1.3.5 - рецензування освітньої програми, посібника, підручника іншого закладу", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.3.6": {"text": "1.3.6 - підвищення кваліфікації (стажування)", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    
    # 1.4 - 1.6 Інша діяльність
    "1.4": {"text": "1.4 - Залучення роботодавців до реалізації освітнього процесу", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.5": {"text": "1.5 - Залучення студентів до неформальної / інформальної освіти", "weight": 5, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.6.1": {"text": "1.6.1 - проведення профорієнтаційних заходів з учнівською та студентською молоддю", "weight": 5, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
    "1.6.2": {"text": "1.6.2 - організація та проведення в Університеті олімпіад, конкурсів для молоді", "weight": 60, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 1},
}

# --- БЛОК 2 ---
# quantity - кількість (n)
# language_coefficient - мовний коефіцієнт (k)
# share - частка роботи викладача (S)
INDICATORS_BLOCK_2 = {
    # 2.1 Публікації
    "2.1.1": {"text": "2.1.1 - наукова публікація у періодичному виданні (Scopus/WoS)", "weight": 300, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.1.2.1": {"text": "2.1.2.1 - наукова публікація (фахове видання України, категорія А)", "weight": 150, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.1.2.2": {"text": "2.1.2.2 - наукова публікація (фахове видання України, категорія Б)", "weight": 100, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.1.3": {"text": "2.1.3 - наукова публікація (не включена до фахових видань)", "weight": 85, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    
    # 2.2 Індекс Гірша
    "2.2.1.1": {"text": "2.2.1.1 - Збільшення індексу Гірша (Scopus, WoS) на 1", "weight": 200, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.1.2": {"text": "2.2.1.2 - Збільшення індексу Гірша (Scopus, WoS) з 1 на 2", "weight": 500, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.1.3": {"text": "2.2.1.3 - Збільшення індексу Гірша (Scopus, WoS) з 2 на 3 (і більше)", "weight": 1000, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.1.4": {"text": "2.2.1.4 - Збільшення індексу Гірша (Scopus, WoS) з 15 на 16 (і більше)", "weight": 1500, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.2.1": {"text": "2.2.2.1 - Збільшення індексу Гірша (Google Scholar) на 1", "weight": 100, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.2.2": {"text": "2.2.2.2 - Збільшення індексу Гірша (Google Scholar) з 1 на 5", "weight": 250, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.2.3": {"text": "2.2.2.3 - Збільшення індексу Гірша (Google Scholar) з 5 на 6 (і більше)", "weight": 500, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.2.2.4": {"text": "2.2.2.4 - Збільшення індексу Гірша (Google Scholar) з 15 на 16 (і більше)", "weight": 750, "formula_type": "fixed_value", "variables": [], "block": 2},
    
    # 2.3 - 2.5 Тези, конференції, видання
    "2.3.1": {"text": "2.3.1 - Наявність тез або доповідей в міжнародному виданні", "weight": 50, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.3.2": {"text": "2.3.2 - Наявність тез або доповідей у всеукраїнському виданні", "weight": 20, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.3.3": {"text": "2.3.3 - Наявність тез або доповідей в університетському виданні", "weight": 15, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.4.1": {"text": "2.4.1 - Участь у міжнародній конференції, виставці, форумі", "weight": 50, "formula_type": "quantity_share", "variables": ["quantity", "share"], "block": 2},
    "2.4.2": {"text": "2.4.2 - Участь у всеукраїнській конференції, виставці, форумі", "weight": 20, "formula_type": "quantity_share", "variables": ["quantity", "share"], "block": 2},
    "2.4.3": {"text": "2.4.3 - Участь в університетській конференції, виставці, форумі", "weight": 15, "formula_type": "quantity_share", "variables": ["quantity", "share"], "block": 2},
    "2.5.1": {"text": "2.5.1 - Видання підручника, що рекомендований МОН", "weight": 400, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.5.2": {"text": "2.5.2 - Видання навчального посібника, що рекомендований МОН", "weight": 350, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.5.3": {"text": "2.5.3 - Видання підручника, що рекомендований вченою радою ЗВО", "weight": 300, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.5.4": {"text": "2.5.4 - Видання навчального посібника, що рекомендований вченою радою ЗВО", "weight": 250, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.5.5": {"text": "2.5.5 - Видання монографії", "weight": 500, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    "2.5.6": {"text": "2.5.6 - Видання наукової чи навчальної літератури іноземною мовою", "weight": 800, "formula_type": "scientific_publication", "variables": ["quantity", "language_coefficient", "share"], "block": 2},
    
    # 2.6 - 2.10 Керівництво та робота у складі комісій
    "2.6.1": {"text": "2.6.1 - Наукове керівництво кандидата наук (PhD)", "weight": 200, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.6.2": {"text": "2.6.2 - Наукове керівництво доктора наук", "weight": 300, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.7": {"text": "2.7 - Участь у міжнародному науковому проєкті / експертизі", "weight": 200, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.1": {"text": "2.8.1 - Робота у складі робочої групи з розроблення ОП", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.2": {"text": "2.8.2 - Робота у складі експертних рад МОН", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.3": {"text": "2.8.3 - Робота у складі галузевих експертних рад НАЗЯВО", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.4": {"text": "2.8.4 - Робота у складі акредитаційної комісії ДСЯО", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.5": {"text": "2.8.5 - Робота у складі експертних комісій ДСЯО / НАЗЯВО", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.6": {"text": "2.8.6 - Робота у складі НМР / НМК з вищої освіти МОН", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.7": {"text": "2.8.7 - Робота у складі робочих груп з розроблення стандартів вищої освіти", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.9": {"text": "2.8.9 - Робота у складі Вченої ради Університету", "weight": 4, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.10": {"text": "2.8.10 - Робота у складі методичної ради Університету", "weight": 3, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.11": {"text": "2.8.11 - Робота у складі ради з якості чи комісії з якості", "weight": 2, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.12": {"text": "2.8.12 - Робота у складі ректорату", "weight": 1, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.13.1": {"text": "2.8.13.1 - Робота в оргкомітеті/журі олімпіад/конкурсів (1 етап)", "weight": 15, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.13.2": {"text": "2.8.13.2 - Робота в оргкомітеті/журі олімпіад/конкурсів (2 етап)", "weight": 30, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.8.14": {"text": "2.8.14 - Робота у складі професійних та/або громадських об’єднань", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.9.1": {"text": "2.9.1 - Виконання функцій гаранта освітньої програми", "weight": 50, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.9.2": {"text": "2.9.2 - Науковий керівник наукової теми з держ. реєстрацією", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.9.3": {"text": "2.9.3 - Відповідальний виконавець наукової теми з держ. реєстрацією", "weight": 40, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.9.4": {"text": "2.9.4 - Головний редактор наукового фахового видання", "weight": 60, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.9.5": {"text": "2.9.5 - Член редакційної колегії наукового фахового видання", "weight": 40, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.9.6": {"text": "2.9.6 - Член редакційної колегії іноземного рецензованого видання", "weight": 70, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.1": {"text": "2.10.1 - Керівництво студентом (участь у 2 етапі олімпіади/конкурсу)", "weight": 80, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.2": {"text": "2.10.2 - Керівництво студентом (призер у 2 етапі олімпіади/конкурсу)", "weight": 100, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.3": {"text": "2.10.3 - Керівництво студентом (участь у спорт. змаганнях міжнар./всеукр. рівня)", "weight": 80, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.4": {"text": "2.10.4 - Керівництво студентом (призер спорт. змагань міжнар./всеукр. рівня)", "weight": 100, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.5": {"text": "2.10.5 - Керівництво постійно діючим студентським науковим/творчим гуртком", "weight": 80, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.6.1": {"text": "2.10.6.1 - Керівництво студентом (публікація у фаховому виданні + міжнар. базі)", "weight": 45, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.6.2": {"text": "2.10.6.2 - Керівництво студентом (публікація у фаховому виданні України)", "weight": 30, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.6.3": {"text": "2.10.6.3 - Керівництво студентом (публікація у нефаховому виданні)", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.7.1": {"text": "2.10.7.1 - Керівництво студентом (учасник міжнародної конференції)", "weight": 20, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.7.2": {"text": "2.10.7.2 - Керівництво студентом (учасник всеукраїнської конференції)", "weight": 15, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.7.3": {"text": "2.10.7.3 - Керівництво студентом (учасник університетської конференції)", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.10.7.4": {"text": "2.10.7.4 - Керівництво школярем (призер олімпіад/МАН)", "weight": 80, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    
    # 2.12 - 2.21 Атестація, звання, нагороди, інше
    "2.12.1": {"text": "2.12.1 - Керівництво спеціалізованою радою із захисту дисертацій", "weight": 100, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.12.2": {"text": "2.12.2 - Офіційний опонент, член спеціалізованої вченої ради", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.12.3": {"text": "2.12.3 - Рецензування дисертацій", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.13.1": {"text": "2.13.1 - Присудження наукового ступеня доктора філософії", "weight": 500, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.13.2": {"text": "2.13.2 - Присудження наукового ступеня доктора наук", "weight": 700, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.13.3": {"text": "2.13.3 - Отримання диплома про вищу освіту", "weight": 300, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.14.1": {"text": "2.14.1 - Присвоєння вченого звання професора", "weight": 200, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.14.2": {"text": "2.14.2 - Присвоєння вченого звання доцента", "weight": 150, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.14.3": {"text": "2.14.3 - Присвоєння вченого звання старшого дослідника", "weight": 100, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.15.1": {"text": "2.15.1 - Організація міжнародної конференції (член оргкомітету)", "weight": 100, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.15.2": {"text": "2.15.2 - Організація всеукраїнської конференції (член оргкомітету)", "weight": 80, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.15.3": {"text": "2.15.3 - Організація університетської конференції (член оргкомітету)", "weight": 50, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.16.1": {"text": "2.16.1 - Участь в програмі академічної мобільності за кордоном", "weight": 60, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.16.2": {"text": "2.16.2 - Налагодження співпраці з іноземною установою", "weight": 20, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.16.3": {"text": "2.16.3 - Участь в міжнародній програмі/співпраця з іноземною організацією", "weight": 20, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.16.4": {"text": "2.16.4 - Отримання гранту для навчання в іноземному ЗВО", "weight": 70, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.17.1": {"text": "2.17.1 - Організація та проведення виховних заходів зі студентами", "weight": 5, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.17.2": {"text": "2.17.2 - Організація виховних заходів на кураторських годинах", "weight": 3, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.17.3": {"text": "2.17.3 - Проведення чергування в гуртожитках", "weight": 1, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.18": {"text": "2.18 - Досвід практичної роботи за спеціальністю не менше 5 років", "weight": 50, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.19": {"text": "2.19 - Наукове консультування установ протягом не менше 3 років", "weight": 30, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    
    # 2.20 Звання та нагороди
    "2.20.1": {"text": "2.20.1 - Академік НАНУ", "weight": 500, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.2": {"text": "2.20.2 - Член кореспондент НАНУ", "weight": 500, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.3": {"text": "2.20.3 - Членство в галузевих академіях (державних)", "weight": 250, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.4": {"text": "2.20.4 - Членство в громадських академіях", "weight": 80, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.5": {"text": "2.20.5 - Почесне звання Заслуженого професора Університету", "weight": 150, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.6": {"text": "2.20.6 - Почесне звання професора Університету", "weight": 100, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.7": {"text": "2.20.7 - Лауреат Державної премії, премії Президента для молодих вчених", "weight": 250, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.8": {"text": "2.20.8 - Заслужений діяч науки і техніки", "weight": 250, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.9": {"text": "2.20.9 - Заслужений економіст, винахідник тощо", "weight": 250, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.10": {"text": "2.20.10 - Заслужений працівник освіти/іншої галузі", "weight": 200, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.11": {"text": "2.20.11 - Почесна Грамота, Грамота ВР, КМУ, МОНУ", "weight": 100, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.12": {"text": "2.20.12 - Нагрудний знак, орден, медаль", "weight": 150, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.13": {"text": "2.20.13 - Почесна грамота ОДА, обласної ради", "weight": 80, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.14": {"text": "2.20.14 - Премія ОДА та обласної ради", "weight": 100, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.15": {"text": "2.20.15 - Подяка МОНУ", "weight": 50, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.16.1": {"text": "2.20.16.1 - Подяка Обласної державної адміністрації", "weight": 40, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.16.2": {"text": "2.20.16.2 - Подяка Обласної ради", "weight": 30, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.16.3": {"text": "2.20.16.3 - Подяка Міського Голови", "weight": 20, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.17": {"text": "2.20.17 - Подяка Департаментів", "weight": 30, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.18": {"text": "2.20.18 - Почесна грамота УЕП, іншого ЗВО", "weight": 20, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.19": {"text": "2.20.19 - Грамота УЕП, іншого ЗВО", "weight": 10, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.20": {"text": "2.20.20 - Подяка УЕП, іншого ЗВО", "weight": 5, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.21": {"text": "2.20.21 - Звання «Майстер спорту»", "weight": 200, "formula_type": "fixed_value", "variables": [], "block": 2},
    "2.20.22": {"text": "2.20.22 - Звання «Кандидат в майстри спорту»", "weight": 100, "formula_type": "fixed_value", "variables": [], "block": 2},
    
    "2.21.1": {"text": "2.21.1 - Отримання патенту на винахід чи корисну модель", "weight": 20, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
    "2.21.2": {"text": "2.21.2 - Отримання свідоцтва про реєстрацію авторського права", "weight": 10, "formula_type": "simple_multiplication", "variables": ["quantity"], "block": 2},
}

# --- АДМІНІСТРАТИВНІ ПОСАДИ (Блок 2.11) ---
ADMINISTRATIVE_POSITIONS = [
    {"id": "2.11.1", "text": "2.11.1 - ректор", "weight": 300},
    {"id": "2.11.2", "text": "2.11.2 - проректор", "weight": 200},
    {"id": "2.11.3", "text": "2.11.3 - директор коледжу", "weight": 200},
    {"id": "2.11.4", "text": "2.11.4 - директор ліцею", "weight": 100},
    {"id": "2.11.5", "text": "2.11.5 - завідувач кафедри / голова циклової комісії", "weight": 100},
    {"id": "2.11.6", "text": "2.11.6 - відповідальний секретар приймальної комісії", "weight": 50},
    {"id": "2.11.7", "text": "2.11.7 - член приймальної комісії", "weight": 30},
    {"id": "2.11.8", "text": "2.11.8 - Голова вченої ради Університету", "weight": 200},
    {"id": "2.11.9", "text": "2.11.9 - Секретар вченої ради Університету", "weight": 100},
    {"id": "2.11.10", "text": "2.11.10 - Голова методичної ради Університету", "weight": 100},
    {"id": "2.11.11", "text": "2.11.11 - Секретар методичної ради Університету", "weight": 50},
    {"id": "2.11.12", "text": "2.11.12 - Голова атестаційної комісії Університету", "weight": 100},
    {"id": "2.11.13", "text": "2.11.13 - Секретар атестаційної комісії Університету", "weight": 50},
    {"id": "2.11.14", "text": "2.11.14 - Керівник ВВЗЯО", "weight": 100},
    {"id": "2.11.15", "text": "2.11.15 - Керівник центру ІТ", "weight": 100},
    {"id": "2.11.16", "text": "2.11.16 - Голова комісії з академічної доброчесності та етики", "weight": 100},
    {"id": "2.11.17", "text": "2.11.17 - Психологічна служба", "weight": 100},
    {"id": "2.11.18", "text": "2.11.18 - Інша робота", "weight": 50},
]

ALL_INDICATORS = INDICATORS_BLOCK_1.copy()
ALL_INDICATORS.update(INDICATORS_BLOCK_2)

def get_indicator_choices():
    grouped_choices = collections.OrderedDict([('Блок 1', []), ('Блок 2', [])])

    def sort_key(item_key):
        parts = item_key.split('.')
        key_tuple = []
        for part in parts:
            try:
                key_tuple.append(int(part))
            except ValueError:
                key_tuple.append(float('inf'))
                key_tuple.append(part)
        key_tuple.append(ALL_INDICATORS[item_key]['block'])
        return tuple(key_tuple)

    sorted_keys = sorted(ALL_INDICATORS.keys(), key=sort_key)

    for key in sorted_keys:
        details = ALL_INDICATORS[key]
        block_num = details['block']
        block_name = f"Блок {block_num}"
        option_text = f"{details['text']} (Бали: {details['weight']})"
        inputs_str = ",".join(details['variables'])
        grouped_choices[block_name].append(
            {'value': key, 'text': option_text, 'inputs': inputs_str}
        )

    return grouped_choices


def get_indicator_details(indicator_id):
    return ALL_INDICATORS.get(indicator_id)