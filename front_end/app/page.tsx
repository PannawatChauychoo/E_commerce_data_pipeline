import PipelineVisualization from '@/components/PipelineVisualization';
import Header from '@/components/Header';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold tracking-tight mb-4">
              Walmart E-commerce Simulation
            </h1>
            <p className="text-xl text-muted-foreground pt-6">
              A comprehensive data pipeline for e-commerce from data generation to visualization
            </p>
          </div>
          
          <PipelineVisualization />
        </div>
      </main>
    </div>
  );
}
