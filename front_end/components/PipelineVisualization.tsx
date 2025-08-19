import React from 'react';
import Link from 'next/link';
import {
  Database,
  GitBranch,
  LineChart,
  Brain,
  ArrowRight,
  BarChart3,
  Sparkles
} from 'lucide-react';

const PipelineStep = ({
  icon: Icon,
  title,
  description,
  href
}: {
  icon: React.ElementType;
  title: string;
  description: string;
  href?: string;
}) => {
  const content = (
    <div className="border-1 border-[#948979] bg-[#222831] rounded-lg shadow-md w-full h-[200px] text-center transition-all duration-300 hover:shadow-lg hover:scale-105 flex flex-col items-center justify-center">
      <div className="bg-[#393E46] p-2 rounded-full inline-block">
        <Icon className="w-12 h-12 text-[#DFD0B8]" />
      </div>
      <h3 className="mt-4 text-lg font-semibold text-[#DFD0B8]">{title}</h3>
      <p className="text-md text-muted-foreground text-center mt-2">{description}</p>
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="flex flex-col items-center p-2 w-[250px] cursor-pointer">
        {content}
      </Link>
    );
  }

  return (
    <div className="flex flex-col items-center p-2 w-[250px]">
      {content}
    </div>
  );
};

const PipelineVisualization = () => {
  const steps = [
    {
      icon: Brain,
      title: "ABM Simulation",
      description: "Generate synthetic data"
    },
    {
      icon: Database,
      title: "PostgreSQL",
      description: "Store transaction data"
    },
    {
      icon: GitBranch,
      title: "ETL with DBT",
      description: "Transform and model data"
    },
    {
      icon: BarChart3,
      title: "Analytics",
      description: "Process and analyze data",
      href: "/dashboard"
    },
  ];

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, index) => (
        <React.Fragment key={step.title}>
          <PipelineStep {...step} />
          {index < steps.length - 1 && (
            <ArrowRight className="w-16 h-16 text-muted-foreground" />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default PipelineVisualization; 
