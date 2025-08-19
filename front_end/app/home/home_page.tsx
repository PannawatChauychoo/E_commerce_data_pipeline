import PipelineVisualization from "@/components/PipelineVisualization";
import Header from "@/components/Header";
import SimulationWorkspace from "@/components/SimulationVisualization";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#393E46]">
      <Header />
      <main>
        <div className="container mx-auto px-4 py-8 space-y-5">

          <PipelineVisualization />

          <SimulationWorkspace />
        </div>
      </main>
    </div>
  );
}

