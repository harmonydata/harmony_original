mkdir -p output
for f in `ls Evaluate_Model*ipynb`; do
jupyter nbconvert --to notebook --inplace --execute --ExecutePreprocessor.timeout=600 $f
done
