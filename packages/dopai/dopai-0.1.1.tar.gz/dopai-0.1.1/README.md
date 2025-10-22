# Description
DOPai is an intelligent medical assistance tool developed based on Python, leveraging artificial intelligence technology to help clinical doctors diagnose diabetes complicated with osteoporosis. The tool utilizes 12 clinical features to classify diabetic patients into the "Low Bone Mass/Normal Bone Mass Group" or the "Osteoporosis/Severe Osteoporosis Group." Its core functional features include discriminant features such as Age, Gender, ALP, BMI, GNRI, eGFR, SII, FT4, PDW, Creatinine, FT3, and RDW_SD, along with binarization standards for preprocessing: Age > 64.5 → 1 (otherwise 0), Gender = Male → 1 / Female → 0, ALP > 79.8 → 1 (otherwise 0), BMI > 23.6 → 1 (otherwise 0), GNRI > 114.1 → 1 (otherwise 0), eGFR > 106.2 → 1 (otherwise 0), SII > 89.9 → 1 (otherwise 0), FT4 > 19.7 → 1 (otherwise 0), PDW > 14.8 → 1 (otherwise 0), Creatinine > 70.9 → 1 (otherwise 0), FT3 > 5 → 1 (otherwise 0), and RDW_SD > 40.6 → 1 (otherwise 0). By integrating quantitative assessments of these clinical indicators, the tool provides data-driven decision support for early screening and graded diagnosis of osteoporosis.


## Installation and usage


```python
pip install dopai
from dopai.predictor import predictor_dopai

# Input data format:
#    id      Age  Gender  ALP  BMI  GNRI  eGFR  SII  FT4  PDW  Creatinine  FT3  RDW_SD
# 0  1000529    1       0    0    0     0     0    0    0    1           1    0       1
# 1  1008512    0       0    0    1     1     0    1    0    1           1    0       1

predictor_dopai(
    filepath="example.csv",
    baseurl="https://api.ocoolai.com/v1",
    apikey="your API_KEY"
)

```
