import { Card, CardContent } from "@/components/ui/card";
import Header from "@/components/Header";

export default function DocumentationPage() {
  const sections = [
    {
      id: "1",
      title: "Overview",
      subsections: [
        {
          id: "1.1",
          title: "Project Description",
          content: `This project simulates a simplified Walmart-like E-commerce platform from end-to-end:
          • Generate synthetic purchase data using a Python-based Agent-Based Model (ABM)
          • Ingest and store data in a Postgres database, connected via Tailscale
          • Transform and load data within Postgres using dbt
          • Visualize the data pipeline and dashboard in a React/Next.js frontend
          • Use Airflow to orchestrate the entire pipeline at a daily interval`
        },
        {
          id: "1.2",
          title: "Goals and Objectives",
          content: `• Demonstrate a full data pipeline for an E-commerce simulation
          • Provide a realistic environment reflecting operational constraints
          • Enable advanced analysis on transactional data
          • Maintain a well-documented, testable, and modular codebase`
        }
      ]
    },
    {
      id: "2",
      title: "Technical Stack",
      subsections: [
        {
          id: "2.1",
          title: "Technologies Used",
          content: `• Frontend: Javascript, React, Tailwind, Next.js, Lucide icons
          • Testing: Jest
          • Backend: NodeJS, Python, dbt
          • Database: PostgreSQL
          • Orchestration: Airflow`
        },
      ]
    },
    {
      id: "3",
      title: "Architecture",
      subsections: [
        {
          id: "3.1",
          title: "System Components",
          content: `The system consists of several key components:
          • Agent-Based Model (ABM) for synthetic data generation
          • Remote PostgreSQL database for data storage
          • dbt for data transformation
          • Airflow for pipeline orchestration
          • React/Next.js frontend for visualization`
        },
        {
          id: "3.2",
          title: "Data Pipeline",
          content: `The data pipeline follows these steps:
          1. ABM generates synthetic transaction data
          2. Data is ingested into PostgreSQL database
          3. dbt performs data transformations
          4. Transformed data is used for analytics and visualization
          5. Airflow orchestrates the entire process on a daily schedule`
        }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-16">
        <div className="max-w-6xl mx-auto p-8">
          <div className="mb-12">
            <h1 className="text-4xl font-bold mb-4">Documentation</h1>
            <p className="text-lg text-muted-foreground">
              Comprehensive documentation of the Walmart E-commerce Simulation project architecture and implementation.
            </p>
          </div>
          
          <div className="space-y-16">
            {sections.map((section) => (
              <div key={section.id} className="space-y-8">
                <h2 className="text-3xl font-semibold border-b pb-2" id={section.id}>
                  {section.id}. {section.title}
                </h2>
                
                {section.subsections.map((subsection) => (
                  <div key={subsection.id} className="space-y-4">
                    <h3 className="text-2xl font-medium" id={subsection.id}>
                      {subsection.id} {subsection.title}
                    </h3>
                    <Card className="hover:shadow-lg transition-shadow duration-200">
                      <CardContent className="pt-6">
                        <div className="prose prose-gray dark:prose-invert max-w-none">
                          {subsection.content.split('\n').map((line, i) => (
                            <p key={i} className="whitespace-pre-wrap mb-2 text-base">
                              {line.trim()}
                            </p>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
} 