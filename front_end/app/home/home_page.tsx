import PipelineVisualization from "@/components/PipelineVisualization";
import Header from "@/components/Header";
import SimulationWorkspace from "@/components/SimulationVisualization";

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <div className="container mx-auto px-6 py-12 space-y-12">
          <div className="text-center space-y-4 mb-12">
            <h1 className="text-4xl font-bold text-foreground">
              E-Commerce Data Pipeline
            </h1>
            <p className="text-lg text-muted-foreground max-w-4xl mx-auto">
              Agent-based simulation with modern data engineering stack:
              PostgreSQL, Airflow, DBT, and PowerBI
            </p>
          </div>

          <PipelineVisualization />
          <SimulationWorkspace />
        </div>
      </main>
    </div>
  );
}

