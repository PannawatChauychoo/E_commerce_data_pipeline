import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, Users, ShoppingCart, TrendingUp } from "lucide-react";

const MetricCard = ({
  title,
  value,
  icon: Icon,
  description
}: {
  title: string;
  value: string;
  icon: React.ElementType;
  description: string;
}) => (
  <Card className="w-full">
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-md font-medium-semibold">
        {title}
      </CardTitle>
      <Icon className="h-6 w-6 text-muted-foreground" />
    </CardHeader>
    <CardContent>
      <div className="text-4xl font-bold">{value}</div>
      <p className="text-xs text-muted-foreground">{description}</p>
    </CardContent>
  </Card>
);

export default function DashboardPage() {
  const metrics = [
    {
      title: "Total Revenue",
      value: "$45,231.89",
      icon: DollarSign,
      description: "+20.1% from last month"
    },
    {
      title: "Active Users",
      value: "2,350",
      icon: Users,
      description: "+180 new users"
    },
    {
      title: "Total Orders",
      value: "12,234",
      icon: ShoppingCart,
      description: "+19% from last week"
    },
    {
      title: "Sales Growth",
      value: "15.3%",
      icon: TrendingUp,
      description: "Monthly increase"
    }
  ];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Overview</h2>
        <p className="text-muted-foreground">
          Overview of your store performance and metrics
        </p>
      </div>

      <div className="grid grid-cols-4 gap-8">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} {...metric} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-7 gap-4">
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle className="text-xl font-medium-semibold">Revenue Over Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px] bg-gray-100 dark:bg-gray-800 rounded-lg">
              {/* Chart will go here */}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-xl font-medium-semibold">Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[250px] bg-gray-100 dark:bg-gray-800 rounded-lg">
              {/* Transaction list will go here */}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 