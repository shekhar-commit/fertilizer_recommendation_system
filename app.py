from flask import Flask, render_template, request
import joblib
import pandas as pd

app = Flask(__name__)

# Load model & encoders
model = joblib.load("fertilizer_model.pkl")
encoders = joblib.load("encoders.pkl")


# ✅ SAFE CONVERSION FUNCTION (ERROR FIX)
def safe_float(value, default=0):
    try:
        if value is None or value.strip() == "":
            return default
        return float(value)
    except:
        return default


# 🔥 Prediction
def predict_fertilizer(data):
    df = pd.DataFrame([data])

    for col in ["Soil", "Crop", "Stage", "Season", "Zone", "Previous_Crop"]:
        df[col] = encoders[col].transform(df[col])

    pred = model.predict(df)
    return encoders["Fertilizer"].inverse_transform(pred)[0]


# 🔥 Recommendation Engine
def recommendation(data):

    fert = predict_fertilizer(data)

    N, P, K = data["N"], data["P"], data["K"]

    # Quantity logic
    quantity = f"{max(0,(50-N)*2)} kg/acre"

    # Timing logic
    if data["Stage"] == "Seedling":
        timing = "Apply before sowing"
    elif data["Stage"] == "Vegetative":
        timing = "Apply during early growth stage"
    elif data["Stage"] == "Flowering":
        timing = "Apply before flowering"
    else:
        timing = "Minimal fertilizer needed"

    # Method logic
    if fert in ["Urea", "DAP"]:
        method = "Broadcast with irrigation"
    elif fert == "Potassium Nitrate":
        method = "Foliar spray"
    else:
        method = "Soil application"

    # Yield estimation
    yield_est = "25–30 quintal/acre (approx)"

    return {
        "fertilizer": fert,
        "quantity": quantity,
        "timing": timing,
        "method": method,
        "yield": yield_est,
        "advice": f"Using {fert} properly will improve crop health and increase yield."
    }


# 🟢 ROUTES

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():

    data = {
        "Soil": request.form.get("soil"),
        "Crop": request.form.get("crop"),
        "Stage": request.form.get("stage"),
        "Season": request.form.get("season"),
        "Zone": request.form.get("zone"),

        "N": safe_float(request.form.get("N")),
        "P": safe_float(request.form.get("P")),
        "K": safe_float(request.form.get("K")),
        "pH": safe_float(request.form.get("pH")),

        "Temp": safe_float(request.form.get("temp")),
        "Humidity": safe_float(request.form.get("humidity")),
        "Rainfall": safe_float(request.form.get("rainfall")),

        "Last_Fert_Days": int(safe_float(request.form.get("last_fert"))),
        "Last_Irrigation_Days": int(safe_float(request.form.get("last_irrigation"))),

        "Previous_Crop": request.form.get("prev_crop")
    }

    result = recommendation(data)

    return render_template("result.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)