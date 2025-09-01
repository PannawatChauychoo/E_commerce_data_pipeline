# 🛒 Walmart E-Commerce Simulation

![Main Page](./Main_page.png)

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" />
  <img src="https://img.shields.io/badge/Tech-PostgreSQL-blue?style=flat-square&logo=postgresql" />
  <img src="https://img.shields.io/badge/Tech-Python-yellow?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Tech-DBT-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Tech-Airflow-lightblue?style=flat-square&logo=apache-airflow" />
  <img src="https://img.shields.io/badge/Tech-Next.js-black?style=flat-square&logo=nextdotjs" />
  <img src="https://img.shields.io/badge/Tech-Django-green?style=flat-square&logo=django" />
</p>

This project is a **portfolio showcase** simulating Walmart’s e-commerce ecosystem.  
It highlights **data engineering, analytics, and full‑stack development skills** through synthetic data, pipelines, APIs, and dashboards.  

---

## ✨ What This Project Demonstrates

- **Data Engineering Skills**  
  Building a warehouse with fact/dim schema, orchestrating pipelines with Airflow, and applying incremental DBT models.  

- **Data Science & Analytics**  
  Simulating customer behavior, segmenting users, and tracking KPIs like CLV, AOV, and stock‑out rates.  

- **Full‑Stack Development**  
  Designing a Django REST API backend and an interactive Next.js dashboard for real‑time monitoring.  

---

## 🚀 Features

- 📦 **Synthetic Datasets** – customers, products, transactions, commerce metadata  
- 🗄 **Database + ETL** – PostgreSQL + DBT + Airflow  
- 💻 **Backend** – Django REST API for simulation & analytics  
- 🎨 **Frontend** – Next.js + Tailwind + ShadcnUI interactive dashboards  
- 📊 **Dashboards** – CLV, AOV, stockout rate, category spend, time series  

---

## 📖 Visual Documentation

![Documentation](./Documentation.png)

- **Backend Flow:**  
  ![Backend Structure](./backend_structure.png)

- **Frontend Flow:**  
  ![Frontend Structure](./frontend_structure.png)

---

## 🖥 Example Dashboard

![Dashboard](./Dashboard.png)

---

## ⚙️ How to Run (Simplified)

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/walmart-simulation.git
   cd walmart-simulation
   ```

2. **Start backend**
   ```bash
   cd backend
   docker-compose up --build
   ```

3. **Start frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the project**
   - API → [http://localhost:8000/api](http://localhost:8000/api)  
   - Dashboard → [http://localhost:3000](http://localhost:3000)  

---

## 📈 Roadmap

- [ ] Add recommendation system (collaborative filtering)  
- [ ] Extend supply chain simulation (suppliers → warehouses → retail)  
- [ ] Deploy cloud demo version  
- [ ] Add Power BI / Grafana connectors  

---

## 👨‍💻 Author

This project was created as part of a **Data Science & Analytics portfolio** to demonstrate:  
- Strong SQL & data modeling foundations  
- Ability to design scalable data pipelines  
- Experience in building interactive dashboards and APIs  

---

## 📜 License

MIT License – free to use and adapt.  
