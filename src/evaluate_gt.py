import csv
from pathlib import Path
from sklearn.metrics import classification_report, accuracy_score

BASE_DIR = Path(__file__).resolve().parent.parent
GT_FILE = BASE_DIR / 'data' / 'processed' / 'ground_truth_final.csv'
NORM_FILE = BASE_DIR / 'data' / 'processed' / 'chat_normalized.csv'

def run():
    from src.predict import predict_single_text

    if not GT_FILE.exists() or not NORM_FILE.exists():
        print('[ERROR] File ground_truth_final.csv atau chat_normalized.csv tidak ditemukan.')
        return

    with open(GT_FILE, 'r', encoding='utf-8-sig') as f:
        gt_rows = list(csv.DictReader(f))
    with open(NORM_FILE, 'r', encoding='utf-8-sig') as f:
        norm_rows = list(csv.DictReader(f))

    text_map = {r['sub_conversation_id']: r.get('normalized_text', r.get('clean_text', '')) for r in norm_rows}
    y_true, y_pred, matches = [], [], []

    for r in gt_rows:
        sub_id = r.get('sub_conversation_id')
        gt_label = r.get('kategori_kendala_final')
        if sub_id in text_map and text_map[sub_id].strip():
            pred_res = predict_single_text(text_map[sub_id])
            pred_label = pred_res['predicted_category']
            y_true.append(gt_label)
            y_pred.append(pred_label)
            matches.append(gt_label == pred_label)

    acc = accuracy_score(y_true, y_pred)
    print('=' * 60)
    print('  HASIL EVALUASI AKURASI PREDIKSI MODEL VS GROUND TRUTH')
    print('=' * 60)
    print(f'Total sampel percakapan : {len(y_true)}')
    print(f'Jumlah Prediksi Tepat   : {sum(matches)}')
    print(f'Jumlah Prediksi Salah   : {len(y_true) - sum(matches)}')
    print(f"Akurasi Keseluruhan     : {acc * 100:.2f}%")
    print('CLASSIFICATION REPORT DETIL (PREDIKSI VS GROUND TRUTH):')
    print(classification_report(y_true, y_pred, zero_division=0))

if __name__ == '__main__':
    run()
