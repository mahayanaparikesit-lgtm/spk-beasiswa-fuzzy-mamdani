## Validasi manual vs program

### M09 Indah (tumpang tindih): IPK=3.3, penghasilan=3.5, tanggungan=4, prestasi=62

- Fuzzifikasi: IPK(R,S,T)=(0.0000, 0.4000, 0.6000); Penghasilan(R,S,T)=(0.2500, 0.7500, 0.0000); Tanggungan(Sd,S,B)=(0.0000, 0.5000, 0.5000); Prestasi(R,S,T)=(0.0000, 0.4000, 0.6000)
- α aktif: R4=0.2500→L, R5=0.4000→CL, R7=0.2500→SL, R8=0.6000→L, R14=0.4000→CL, R15=0.4000→L, R17=0.5000→L, R18=0.5000→SL, R21=0.2500→L, R22=0.6000→L
- Tinggi potongan: TL=0.0000, CL=0.4000, L=0.6000, SL=0.5000
- Centroid: Σμz / Σμ = 23044.1750 / 348.2500 = 66.1714
- **Manual = 66.171357; Program = 66.171357; selisih = 1.28e-13; scikit-fuzzy = 66.147031**

### M13 Maya (bertentangan): IPK=2.1, penghasilan=0.8, tanggungan=7, prestasi=25

- Fuzzifikasi: IPK(R,S,T)=(1.0000, 0.0000, 0.0000); Penghasilan(R,S,T)=(1.0000, 0.0000, 0.0000); Tanggungan(Sd,S,B)=(0.0000, 0.0000, 1.0000); Prestasi(R,S,T)=(1.0000, 0.0000, 0.0000)
- α aktif: R1=1.0000→CL, R12=1.0000→CL, R19=1.0000→TL, R21=1.0000→L
- Tinggi potongan: TL=1.0000, CL=1.0000, L=1.0000, SL=0.0000
- Centroid: Σμz / Σμ = 23791.6500 / 650.5000 = 36.5744
- **Manual = 36.574404; Program = 36.574404; selisih = 0.00e+00; scikit-fuzzy = 36.602564**

### M17 Rizky (normal): IPK=3.45, penghasilan=5.2, tanggungan=3, prestasi=66

- Fuzzifikasi: IPK(R,S,T)=(0.0000, 0.1000, 0.9000); Penghasilan(R,S,T)=(0.0000, 1.0000, 0.0000); Tanggungan(Sd,S,B)=(0.0000, 1.0000, 0.0000); Prestasi(R,S,T)=(0.0000, 0.2000, 0.8000)
- α aktif: R5=0.1000→CL, R8=0.9000→L, R14=0.2000→CL, R17=0.8000→L, R22=0.8000→L
- Tinggi potongan: TL=0.0000, CL=0.2000, L=0.9000, SL=0.0000
- Centroid: Σμz / Σμ = 14350.0000 / 238.0000 = 60.2941
- **Manual = 60.294118; Program = 60.294118; selisih = 6.39e-14; scikit-fuzzy = 60.294118**

### M12 Lukman (bertentangan): IPK=3.9, penghasilan=12.0, tanggungan=2, prestasi=85

- Fuzzifikasi: IPK(R,S,T)=(0.0000, 0.0000, 1.0000); Penghasilan(R,S,T)=(0.0000, 0.0000, 1.0000); Tanggungan(Sd,S,B)=(0.5000, 0.5000, 0.0000); Prestasi(R,S,T)=(0.0000, 0.0000, 1.0000)
- α aktif: R9=1.0000→CL, R16=0.5000→CL, R17=0.5000→L, R20=0.5000→TL, R22=1.0000→L
- Tinggi potongan: TL=0.5000, CL=1.0000, L=1.0000, SL=0.0000
- Centroid: Σμz / Σμ = 21520.8250 / 500.2500 = 43.0201
- **Manual = 43.020140; Program = 43.020140; selisih = 2.13e-14; scikit-fuzzy = 43.041667**
