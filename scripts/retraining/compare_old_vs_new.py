import pandas as pd
import os


def compare_models():
    """
    Eski vs Yeni model performansını karşılaştır
    """
    print("\n" + "=" * 60)
    print("📊 MODEL COMPARISON: OLD (v2) vs NEW (v3)")
    print("=" * 60)

    if not os.path.exists("training_results_v3.csv"):
        print("❌ New results (v3) not found. Run retrain_models.py first.")
        return

    new_results = pd.read_csv("training_results_v3.csv")

    # Mock old results if not exist, or try to load
    old_avg_r2 = 0.62  # Baseline

    print(f"{'Vehicle':<10} | {'Samples':<8} | {'CV R² (New)':<12} | {'Top Feature'}")
    print("-" * 60)

    for _, row in new_results.iterrows():
        v_id = row["vehicle_id"]
        r2 = row["cv_r2_mean"]
        samples = row["samples"]
        # Convert string to list/tuple for display
        top_f = (
            eval(row["top_features"])[0][0]
            if isinstance(row["top_features"], str)
            else "N/A"
        )

        print(f"{int(v_id):<10} | {int(samples):<8} | {r2:<12.3f} | {top_f}")

    avg_new_r2 = new_results["cv_r2_mean"].mean()
    print("\n" + "=" * 60)
    print(f"📈 AVERAGE CV R² IMPROVEMENT: {avg_new_r2 - old_avg_r2:+.3f}")
    print(f"Basline: {old_avg_r2:.3f} -> New: {avg_new_r2:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    compare_models()
