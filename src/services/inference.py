import pickle
import numpy as np

# Load model sekali saat import
with open("models/dass_classifier.pkl", "rb") as f:
    MODEL = pickle.load(f)

# Mapping level → pesan
LEVEL_MESSAGES = {
    "normal":    "Tidak ada gejala klinis.",
    "mild":      "Gejala ringan, pertimbangkan konseling.",
    "moderate":  "Gejala sedang, disarankan sesi dengan psikolog.",
    "severe":    "Gejala berat, segera konsultasi psikiater.",
    "extremely": "Gejala sangat berat, perlu perhatian medis segera."
}

LEVEL_ADVICE = {
    "normal": "Hasil Anda menunjukkan bahwa kondisi mental Anda saat ini tergolong sehat. Tetap pertahankan kebiasaan baik seperti olahraga teratur, pola makan seimbang, dan istirahat yang cukup untuk menjaga kesehatan mental Anda.",
    "mild": "Hasil Anda menunjukkan adanya gejala ringan. Cobalah untuk menerapkan teknik relaksasi seperti mindfulness, meditasi, atau menulis jurnal. Berbicara dengan teman, keluarga, atau konselor juga bisa sangat membantu.",
    "moderate": "Anda mengalami gejala tingkat sedang. Sangat disarankan untuk menjadwalkan sesi konsultasi dengan psikolog atau terapis. Terapi perilaku kognitif (CBT) dan pendekatan terapi lainnya bisa sangat efektif untuk kondisi Anda.",
    "severe": "Gejala yang Anda alami tergolong berat. Penting untuk segera mencari bantuan profesional. Silakan berkonsultasi dengan psikiater atau psikolog klinis untuk mendapatkan diagnosis dan rencana penanganan yang tepat, yang mungkin meliputi terapi dan/atau obat-obatan.",
    "extremely": "Hasil Anda menunjukkan gejala yang sangat berat dan memerlukan perhatian medis segera. Silakan hubungi hotline krisis atau kunjungi unit gawat darurat terdekat. Psikiater dapat memberikan perawatan darurat yang Anda butuhkan."
}

def predict_dass(dep: list[int], anx: list[int], strss: list[int]) -> dict:
    # Gabung semua skor
    x = np.array([sum(dep), sum(anx), sum(strss)]).reshape(1, -1)
    pred = MODEL.predict(x)[0]      
    return {
        "level": pred,
        "message": LEVEL_MESSAGES.get(pred, ""),
        "advice": LEVEL_ADVICE.get(pred, "")
    }
