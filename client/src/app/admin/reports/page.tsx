"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { reportActions } from "@/lib/actions";
import { SalesReportData, InventoryReportData, ReportConfig, ReportType, AiGeneratedReport } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import {
  BarChart3,
  Package,
  TrendingUp,
  AlertTriangle,
  DollarSign,
  ShoppingBag,
  Calendar,
  Save,
  Play,
  Trash2,
  Edit,
  Plus,
  FileText,
  Clock,
  BookmarkPlus,
  Sparkles,
  RefreshCw,
  XCircle,
  TrendingDown,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ReportDisplay, SalesReportDisplay, InventoryReportDisplay, ProductPerformanceDisplay, LowStockReportDisplay, DownloadableReport } from "@/components/reports/report-display";
import { AiAnalysisCard } from "@/components/reports/ai-analysis-card";

// Type for dynamic report data
type ReportData = SalesReportData | InventoryReportData | Record<string, unknown>;

export default function AdminReportsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("ai-reports");

  // Auth token state
  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  // Autonomous AI Reports State
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiGeneratingType, setAiGeneratingType] = useState<string | null>(null);
  const [aiReportResult, setAiReportResult] = useState<AiGeneratedReport | null>(null);

  // Default dates for quick reporting
  const todayStr = new Date().toISOString().split("T")[0];
  const thirtyDaysAgoStr = new Date(Date.now() - 30 * 86400000).toISOString().split("T")[0];

  // AI parameters state
  const [aiSalesStart, setAiSalesStart] = useState(thirtyDaysAgoStr);
  const [aiSalesEnd, setAiSalesEnd] = useState(todayStr);
  const [aiSalesGroupBy, setAiSalesGroupBy] = useState<"day" | "week" | "month">("day");

  const [aiInventoryLowStockOnly, setAiInventoryLowStockOnly] = useState(false);

  const [aiPerfStart, setAiPerfStart] = useState(thirtyDaysAgoStr);
  const [aiPerfEnd, setAiPerfEnd] = useState(todayStr);
  const [aiPerfTopN, setAiPerfTopN] = useState(10);

  const [aiLowStockThreshold, setAiLowStockThreshold] = useState(20);

  // Saved Reports State
  const [savedReports, setSavedReports] = useState<ReportConfig[]>([]);
  const [isLoadingSaved, setIsLoadingSaved] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingReport, setEditingReport] = useState<ReportConfig | null>(null);
  const [runReportData, setRunReportData] = useState<ReportData | null>(null);
  const [runReportType, setRunReportType] = useState<ReportType | null>(null);
  const [runningReportId, setRunningReportId] = useState<number | null>(null);

  // New Report Form State
  const [newReportName, setNewReportName] = useState("");
  const [newReportType, setNewReportType] = useState<ReportType>("SALES");
  const [newReportDescription, setNewReportDescription] = useState("");
  const [newReportParams, setNewReportParams] = useState<Record<string, string>>({});

  // Sales Report State
  const [salesStartDate, setSalesStartDate] = useState(thirtyDaysAgoStr);
  const [salesEndDate, setSalesEndDate] = useState(todayStr);
  const [salesGroupBy, setSalesGroupBy] = useState<"day" | "week" | "month">("day");
  const [salesReport, setSalesReport] = useState<SalesReportData | null>(null);

  // Inventory Report State
  const [inventoryLowStockOnly, setInventoryLowStockOnly] = useState(false);
  const [inventoryReport, setInventoryReport] = useState<InventoryReportData | null>(null);

  // Product Performance State
  const [perfStartDate, setPerfStartDate] = useState(thirtyDaysAgoStr);
  const [perfEndDate, setPerfEndDate] = useState(todayStr);
  const [perfTopN, setPerfTopN] = useState(10);
  const [perfReport, setPerfReport] = useState<Record<string, unknown> | null>(null);

  // Low Stock Report State
  const [lowStockThreshold, setLowStockThreshold] = useState(20);
  const [lowStockReport, setLowStockReport] = useState<Record<string, unknown> | null>(null);

  // Load saved reports on mount
  useEffect(() => {
    if (authToken !== null) {
      loadSavedReports();
    }
  }, [authToken]);

  const loadSavedReports = async () => {
    setIsLoadingSaved(true);
    try {
      const response = await reportActions.getAll(0, 100, authToken);
      setSavedReports(response.reports);
    } catch (error) {
      console.error("Failed to load saved reports:", error);
    } finally {
      setIsLoadingSaved(false);
    }
  };

  const handleGenerateAiReport = async (
    type: "sales" | "inventory" | "product-performance" | "low-stock" | "sales-prediction",
    params?: Record<string, unknown>
  ) => {
    setIsAiLoading(true);
    setAiGeneratingType(type);
    try {
      const result = await reportActions.generateAiReport(type, params, authToken);
      setAiReportResult(result);
      toast.success(`Autonomous AI ${type.replace("-", " ")} report generated!`);
      // Scroll smoothly down to results
      setTimeout(() => {
        const el = document.getElementById("ai-report-results-anchor");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (error) {
      console.error("Failed to generate AI report:", error);
      toast.error(error instanceof Error ? error.message : "Failed to generate AI report");
    } finally {
      setIsAiLoading(false);
      setAiGeneratingType(null);
    }
  };

  const createReport = async () => {
    if (!newReportName) {
      toast.error("Please enter a report name");
      return;
    }

    if ((newReportType === "SALES" || newReportType === "PRODUCT_PERFORMANCE") && !validateDateRange(newReportParams.start_date, newReportParams.end_date)) {
      return;
    }

    setIsLoading(true);
    try {
      let parameters: Record<string, unknown> = {};

      if (newReportType === "SALES" || newReportType === "PRODUCT_PERFORMANCE") {
        parameters = {
          start_date: newReportParams.start_date,
          end_date: newReportParams.end_date,
          group_by: newReportParams.group_by || "day",
          top_n: parseInt(newReportParams.top_n || "10"),
        };
      } else if (newReportType === "INVENTORY") {
        parameters = {
          low_stock_only: newReportParams.low_stock_only === "true",
        };
      } else if (newReportType === "LOW_STOCK") {
        parameters = {
          threshold_percentage: parseInt(newReportParams.threshold_percentage || "20"),
        };
      }

      await reportActions.create(
        {
          report_name: newReportName,
          report_type: newReportType,
          description: newReportDescription || undefined,
          parameters,
        },
        authToken,
      );

      toast.success("Report configuration saved!");
      setShowCreateDialog(false);
      resetNewReportForm();
      loadSavedReports();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save report");
    } finally {
      setIsLoading(false);
    }
  };

  const updateReport = async () => {
    if (!editingReport) return;

    setIsLoading(true);
    try {
      await reportActions.update(
        editingReport.report_id,
        {
          report_name: newReportName,
          description: newReportDescription || undefined,
          parameters: newReportParams as Record<string, unknown>,
        },
        authToken,
      );

      toast.success("Report updated!");
      setShowEditDialog(false);
      setEditingReport(null);
      resetNewReportForm();
      loadSavedReports();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update report");
    } finally {
      setIsLoading(false);
    }
  };

  const deleteReport = async (id: number) => {
    if (!confirm("Are you sure you want to delete this report configuration?")) return;

    try {
      await reportActions.delete(id, authToken);
      toast.success("Report deleted");
      loadSavedReports();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete report");
    }
  };

  const runSavedReport = async (report: ReportConfig) => {
    setRunningReportId(report.report_id);
    setRunReportData(null);
    setRunReportType(null);
    try {
      const data = await reportActions.run(report.report_id, undefined, authToken);
      setRunReportData(data);
      setRunReportType(report.report_type);
      toast.success(`Report "${report.report_name}" generated!`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to run report");
    } finally {
      setRunningReportId(null);
    }
  };

  const resetNewReportForm = () => {
    setNewReportName("");
    setNewReportType("SALES");
    setNewReportDescription("");
    setNewReportParams({});
  };

  const openEditDialog = (report: ReportConfig) => {
    setEditingReport(report);
    setNewReportName(report.report_name);
    setNewReportDescription(report.description || "");
    setNewReportParams((report.parameters as Record<string, string>) || {});
    setShowEditDialog(true);
  };

  const saveCurrentReportAsConfig = async (type: ReportType, params: Record<string, unknown>) => {
    if ((type === "SALES" || type === "PRODUCT_PERFORMANCE") && !validateDateRange(params.start_date as string | undefined, params.end_date as string | undefined)) {
      return;
    }

    const name = prompt("Enter a name for this saved report:");
    if (!name) return;

    try {
      await reportActions.create(
        {
          report_name: name,
          report_type: type,
          parameters: params,
        },
        authToken,
      );
      toast.success("Report configuration saved!");
      loadSavedReports();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save report");
    }
  };

  const validateDateRange = (startDate?: string, endDate?: string) => {
    if (!startDate || !endDate) {
      toast.error("Please select start and end dates");
      return false;
    }

    if (new Date(startDate) > new Date(endDate)) {
      toast.error("Start date must be earlier than or equal to end date");
      return false;
    }

    return true;
  };

  const generateSalesReport = async () => {
    if (!validateDateRange(salesStartDate, salesEndDate)) {
      return;
    }

    setIsLoading(true);
    try {
      const report = await reportActions.generateSales(
        {
          start_date: salesStartDate,
          end_date: salesEndDate,
          group_by: salesGroupBy,
        },
        authToken,
      );
      setSalesReport(report);
      toast.success("Sales report generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate report");
    } finally {
      setIsLoading(false);
    }
  };

  const generateInventoryReport = async () => {
    setIsLoading(true);
    try {
      const report = await reportActions.generateInventory(
        {
          low_stock_only: inventoryLowStockOnly,
        },
        authToken,
      );
      setInventoryReport(report);
      toast.success("Inventory report generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate report");
    } finally {
      setIsLoading(false);
    }
  };

  const generatePerformanceReport = async () => {
    if (!validateDateRange(perfStartDate, perfEndDate)) {
      return;
    }

    setIsLoading(true);
    try {
      const report = await reportActions.generateProductPerformance(
        {
          start_date: perfStartDate,
          end_date: perfEndDate,
          top_n: perfTopN,
        },
        authToken,
      );
      setPerfReport(report as Record<string, unknown>);
      toast.success("Performance report generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate report");
    } finally {
      setIsLoading(false);
    }
  };

  const generateLowStockReport = async () => {
    setIsLoading(true);
    try {
      const report = await reportActions.generateLowStock(
        {
          threshold_percentage: lowStockThreshold,
        },
        authToken,
      );
      setLowStockReport(report as Record<string, unknown>);
      toast.success("Low stock report generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate report");
    } finally {
      setIsLoading(false);
    }
  };

  const getReportTypeColor = (type: ReportType) => {
    switch (type) {
      case "SALES":
        return "bg-green-500/10 text-green-400 border-green-500/30";
      case "INVENTORY":
        return "bg-blue-500/10 text-blue-400 border-blue-500/30";
      case "PRODUCT_PERFORMANCE":
        return "bg-purple-500/10 text-purple-400 border-purple-500/30";
      case "LOW_STOCK":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/30";
    }
  };

  const getReportTypeIcon = (type: ReportType) => {
    switch (type) {
      case "SALES":
        return <TrendingUp className="h-4 w-4" />;
      case "INVENTORY":
        return <Package className="h-4 w-4" />;
      case "PRODUCT_PERFORMANCE":
        return <BarChart3 className="h-4 w-4" />;
      case "LOW_STOCK":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  // Helper to render AI report raw data display
  const renderAiRawData = (report: AiGeneratedReport) => {
    const normType = report.report_type.toLowerCase();
    if (normType === "sales" || normType === "sales-prediction") {
      return <SalesReportDisplay data={report.raw_data as SalesReportData} />;
    } else if (normType === "inventory") {
      return <InventoryReportDisplay data={report.raw_data as InventoryReportData} />;
    } else if (normType === "product-performance" || normType === "product_performance") {
      return <ProductPerformanceDisplay data={report.raw_data as any} />;
    } else if (normType === "low-stock" || normType === "low_stock") {
      return <LowStockReportDisplay data={report.raw_data as any} />;
    } else {
      return (
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-4">
            <pre className="bg-background/50 p-4 rounded-lg overflow-auto text-sm max-h-[400px]">
              {JSON.stringify(report.raw_data, null, 2)}
            </pre>
          </CardContent>
        </Card>
      );
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-wrap justify-between items-start gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-3xl font-bold tracking-tight">Reports & Analytics</h1>
              <Badge className="bg-orange-500/15 text-orange-400 border-orange-500/30 flex items-center gap-1 text-xs">
                <Sparkles className="h-3 w-3" />
                Gemini Express Mode
              </Badge>
            </div>
            <p className="text-muted-foreground mt-1">
              Autonomous AI-driven intelligence, predictive forecasting, and customizable business reports
            </p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-card/50 border border-border/50 p-1 flex flex-wrap h-auto gap-1">
            <TabsTrigger
              value="ai-reports"
              className="gap-2 data-[state=active]:bg-gradient-to-r data-[state=active]:from-orange-500 data-[state=active]:to-amber-500 data-[state=active]:text-white font-medium shadow-sm"
            >
              <Sparkles className="h-4 w-4" />
              Autonomous AI Reports
            </TabsTrigger>
            <TabsTrigger value="saved" className="gap-2">
              <Save className="h-4 w-4" />
              Saved Reports
            </TabsTrigger>
            <TabsTrigger value="sales" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              Sales
            </TabsTrigger>
            <TabsTrigger value="inventory" className="gap-2">
              <Package className="h-4 w-4" />
              Inventory
            </TabsTrigger>
            <TabsTrigger value="performance" className="gap-2">
              <BarChart3 className="h-4 w-4" />
              Performance
            </TabsTrigger>
            <TabsTrigger value="lowstock" className="gap-2">
              <AlertTriangle className="h-4 w-4" />
              Low Stock
            </TabsTrigger>
          </TabsList>

          {/* ========================================================================= */}
          {/* Autonomous AI Reports Tab                                                 */}
          {/* ========================================================================= */}
          <TabsContent value="ai-reports" className="space-y-6">
            {/* AI Banner */}
            <div className="rounded-2xl border border-orange-500/30 bg-gradient-to-r from-orange-500/10 via-amber-500/5 to-transparent p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="p-2 rounded-xl bg-orange-500/20 text-orange-400">
                      <Sparkles className="h-5 w-5" />
                    </span>
                    <h2 className="text-xl font-bold">Autonomous Business Intelligence</h2>
                  </div>
                  <p className="text-sm text-muted-foreground max-w-2xl">
                    Generate holistic business reports paired with Gemini 2.5 Pro deep reasoning in Express Mode.
                    Each report synthesizes live database metrics into executive summaries, critical risk alerts,
                    and prioritized strategic actions.
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground bg-background/50 px-3 py-2 rounded-lg border border-border/60 self-start md:self-auto">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  Engine: Gemini 2.5 Pro (Autonomous Reasoning)
                </div>
              </div>
            </div>

            {/* 5 Button-Triggered Report Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {/* Card 1: Sales Analysis */}
              <Card className="bg-card/60 border-border/60 hover:border-orange-500/40 transition-all flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-green-500/10 text-green-400">
                      <TrendingUp className="h-5 w-5" />
                    </div>
                    <Badge variant="outline" className="border-green-500/30 text-green-400 text-xs">
                      Sales
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">Sales Analysis & Revenue Audit</CardTitle>
                  <CardDescription className="text-xs">
                    Evaluates revenue turnover, growth velocity, order volumes, and daily performance metrics.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <label className="text-muted-foreground block mb-1">Start Date</label>
                      <Input
                        type="date"
                        value={aiSalesStart}
                        max={aiSalesEnd || undefined}
                        onChange={(e) => setAiSalesStart(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-muted-foreground block mb-1">End Date</label>
                      <Input
                        type="date"
                        value={aiSalesEnd}
                        min={aiSalesStart || undefined}
                        onChange={(e) => setAiSalesEnd(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-muted-foreground text-xs block mb-1">Group By</label>
                    <Select value={aiSalesGroupBy} onValueChange={(v) => setAiSalesGroupBy(v as any)}>
                      <SelectTrigger className="h-8 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="day">Day</SelectItem>
                        <SelectItem value="week">Week</SelectItem>
                        <SelectItem value="month">Month</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    onClick={() =>
                      handleGenerateAiReport("sales", {
                        start_date: aiSalesStart,
                        end_date: aiSalesEnd,
                        group_by: aiSalesGroupBy,
                      })
                    }
                    disabled={isAiLoading}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white gap-2 mt-2 h-9 text-xs"
                  >
                    {isAiLoading && aiGeneratingType === "sales" ? (
                      <>
                        <Spinner className="h-3.5 w-3.5" />
                        Analyzing with Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        Generate AI Sales Report
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Card 2: Inventory Valuation */}
              <Card className="bg-card/60 border-border/60 hover:border-orange-500/40 transition-all flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400">
                      <Package className="h-5 w-5" />
                    </div>
                    <Badge variant="outline" className="border-blue-500/30 text-blue-400 text-xs">
                      Inventory
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">Inventory Valuation & Health</CardTitle>
                  <CardDescription className="text-xs">
                    Audits total stock valuation, category asset allocations, holding costs, and inactive stock.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="p-3 rounded-lg bg-background/50 border border-border/40 flex items-center justify-between">
                    <label htmlFor="ai-inv-low" className="text-xs text-foreground cursor-pointer">
                      Filter to Low Stock Items Only
                    </label>
                    <input
                      type="checkbox"
                      id="ai-inv-low"
                      checked={aiInventoryLowStockOnly}
                      onChange={(e) => setAiInventoryLowStockOnly(e.target.checked)}
                      className="h-4 w-4 rounded border-border cursor-pointer"
                    />
                  </div>
                  <div className="text-xs text-muted-foreground pt-1">
                    Audits current warehouse stock valuation and stock balances in real-time.
                  </div>
                  <Button
                    onClick={() =>
                      handleGenerateAiReport("inventory", {
                        low_stock_only: aiInventoryLowStockOnly,
                      })
                    }
                    disabled={isAiLoading}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white gap-2 mt-2 h-9 text-xs"
                  >
                    {isAiLoading && aiGeneratingType === "inventory" ? (
                      <>
                        <Spinner className="h-3.5 w-3.5" />
                        Analyzing with Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        Generate AI Inventory Report
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Card 3: Product Performance */}
              <Card className="bg-card/60 border-border/60 hover:border-orange-500/40 transition-all flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400">
                      <BarChart3 className="h-5 w-5" />
                    </div>
                    <Badge variant="outline" className="border-purple-500/30 text-purple-400 text-xs">
                      Performance
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">Product Performance & Velocity</CardTitle>
                  <CardDescription className="text-xs">
                    Identifies top-earning SKUs, category volume leaders, sales consistency, and underperformers.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <label className="text-muted-foreground block mb-1">Start Date</label>
                      <Input
                        type="date"
                        value={aiPerfStart}
                        max={aiPerfEnd || undefined}
                        onChange={(e) => setAiPerfStart(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-muted-foreground block mb-1">End Date</label>
                      <Input
                        type="date"
                        value={aiPerfEnd}
                        min={aiPerfStart || undefined}
                        onChange={(e) => setAiPerfEnd(e.target.value)}
                        className="h-8 text-xs"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-muted-foreground text-xs block mb-1">Top N Products</label>
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={aiPerfTopN}
                      onChange={(e) => setAiPerfTopN(parseInt(e.target.value) || 10)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <Button
                    onClick={() =>
                      handleGenerateAiReport("product-performance", {
                        start_date: aiPerfStart,
                        end_date: aiPerfEnd,
                        top_n: aiPerfTopN,
                      })
                    }
                    disabled={isAiLoading}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white gap-2 mt-2 h-9 text-xs"
                  >
                    {isAiLoading && aiGeneratingType === "product-performance" ? (
                      <>
                        <Spinner className="h-3.5 w-3.5" />
                        Analyzing with Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        Generate AI Performance Report
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Card 4: Low Stock Alert */}
              <Card className="bg-card/60 border-border/60 hover:border-orange-500/40 transition-all flex flex-col justify-between">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
                      <AlertTriangle className="h-5 w-5" />
                    </div>
                    <Badge variant="outline" className="border-amber-500/30 text-amber-400 text-xs">
                      Supply Risk
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">Low Stock & Supply Chain Audit</CardTitle>
                  <CardDescription className="text-xs">
                    Pinpoints items below reorder thresholds, out-of-stock items, and generates replenishment orders.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 pt-0">
                  <div>
                    <label className="text-muted-foreground text-xs block mb-1">Threshold Percentage (%)</label>
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={aiLowStockThreshold}
                      onChange={(e) => setAiLowStockThreshold(parseInt(e.target.value) || 20)}
                      className="h-8 text-xs"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Flags products where stock has dropped to or below {aiLowStockThreshold}% of reorder level.
                  </p>
                  <Button
                    onClick={() =>
                      handleGenerateAiReport("low-stock", {
                        threshold_percentage: aiLowStockThreshold,
                      })
                    }
                    disabled={isAiLoading}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white gap-2 mt-2 h-9 text-xs"
                  >
                    {isAiLoading && aiGeneratingType === "low-stock" ? (
                      <>
                        <Spinner className="h-3.5 w-3.5" />
                        Analyzing with Gemini...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-3.5 w-3.5" />
                        Generate AI Low Stock Report
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Card 5: Sales Prediction & Forecasting */}
              <Card className="bg-card/60 border-border/60 hover:border-orange-500/40 transition-all flex flex-col justify-between md:col-span-2 lg:col-span-2">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="p-2.5 rounded-xl bg-gradient-to-br from-orange-500/20 to-amber-500/20 text-orange-400">
                      <Sparkles className="h-5 w-5" />
                    </div>
                    <Badge className="bg-orange-500/20 text-orange-400 border border-orange-500/30 text-xs">
                      Predictive Horizon (30 Days)
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">Sales Prediction & Demand Forecasting</CardTitle>
                  <CardDescription className="text-xs">
                    Autonomous predictive modeling using 60 days of historical sales trajectory to forecast
                    future revenue momentum, stockout risks, and high-margin replenishment opportunities.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 pt-0">
                  <div className="p-3.5 rounded-xl bg-background/60 border border-border/50 text-xs space-y-1.5">
                    <div className="font-semibold text-foreground flex items-center gap-2">
                      <Clock className="h-3.5 w-3.5 text-orange-400" />
                      Prediction Scope & Methodology
                    </div>
                    <p className="text-muted-foreground leading-relaxed">
                      Gemini 2.5 Pro reviews weekly sales velocity, seasonal order momentum, and revenue trends over the
                      past 60 days to formulate predictive growth scenarios and procurement recommendations for the next month.
                    </p>
                  </div>
                  <Button
                    onClick={() => handleGenerateAiReport("sales-prediction")}
                    disabled={isAiLoading}
                    className="w-full bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white gap-2 h-10 text-xs font-semibold shadow-md"
                  >
                    {isAiLoading && aiGeneratingType === "sales-prediction" ? (
                      <>
                        <Spinner className="h-4 w-4" />
                        Generating Predictive Reasoning with Gemini 2.5 Pro...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Run 30-Day Sales Demand & Velocity Forecast
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* AI Report Results Display */}
            <div id="ai-report-results-anchor" />
            {aiReportResult && (
              <div className="space-y-6 pt-6 border-t border-border/60">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <h2 className="text-xl font-bold flex items-center gap-2">
                      Report Results:
                      <span className="capitalize text-orange-400">
                        {aiReportResult.report_type.replace("-", " ")}
                      </span>
                    </h2>
                    <Badge variant="outline" className="text-xs">
                      Generated {new Date(aiReportResult.generated_at).toLocaleTimeString()}
                    </Badge>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setAiReportResult(null)}
                    className="gap-2 text-muted-foreground hover:text-foreground"
                  >
                    <XCircle className="h-4 w-4" />
                    Clear Results
                  </Button>
                </div>

                {/* Gemini 2.5 Pro Executive Analysis Card */}
                <AiAnalysisCard
                  analysis={aiReportResult.ai_analysis}
                  reportType={aiReportResult.report_type}
                />

                {/* Raw Visual Data Display with PDF/Export capabilities */}
                <div className="space-y-3">
                  <h3 className="text-base font-semibold text-muted-foreground">
                    Underlying Business Data & Visual Breakdown
                  </h3>
                  <DownloadableReport
                    fileName={`AI-${aiReportResult.report_type}-Report`}
                    data={aiReportResult.raw_data as Record<string, unknown>}
                    reportType={aiReportResult.report_type.toUpperCase().replace("-", "_")}
                  >
                    {renderAiRawData(aiReportResult)}
                  </DownloadableReport>
                </div>
              </div>
            )}
          </TabsContent>

          {/* ========================================================================= */}
          {/* Saved Reports Tab                                                         */}
          {/* ========================================================================= */}
          <TabsContent value="saved" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold">Saved Report Configurations</h2>
              <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                <DialogTrigger asChild>
                  <Button className="gap-2 bg-orange-500 hover:bg-orange-600">
                    <Plus className="h-4 w-4" />
                    Create Report Config
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-[500px]">
                  <DialogHeader>
                    <DialogTitle>Create Report Configuration</DialogTitle>
                    <DialogDescription>Save a report configuration to run it anytime with one click.</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Report Name *</label>
                      <Input
                        value={newReportName}
                        onChange={(e) => setNewReportName(e.target.value)}
                        placeholder="e.g., Monthly Sales Report"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Report Type *</label>
                      <Select value={newReportType} onValueChange={(v) => setNewReportType(v as ReportType)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="SALES">Sales Report</SelectItem>
                          <SelectItem value="INVENTORY">Inventory Report</SelectItem>
                          <SelectItem value="PRODUCT_PERFORMANCE">Product Performance</SelectItem>
                          <SelectItem value="LOW_STOCK">Low Stock Report</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Description</label>
                      <Textarea
                        value={newReportDescription}
                        onChange={(e) => setNewReportDescription(e.target.value)}
                        placeholder="Optional description..."
                        rows={2}
                      />
                    </div>

                    {(newReportType === "SALES" || newReportType === "PRODUCT_PERFORMANCE") && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-sm font-medium mb-2 block">Start Date *</label>
                          <Input
                            type="date"
                            value={newReportParams.start_date || ""}
                            max={newReportParams.end_date || undefined}
                            onChange={(e) => setNewReportParams({ ...newReportParams, start_date: e.target.value })}
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-2 block">End Date *</label>
                          <Input
                            type="date"
                            value={newReportParams.end_date || ""}
                            min={newReportParams.start_date || undefined}
                            onChange={(e) => setNewReportParams({ ...newReportParams, end_date: e.target.value })}
                          />
                        </div>
                      </div>
                    )}

                    {newReportType === "LOW_STOCK" && (
                      <div>
                        <label className="text-sm font-medium mb-2 block">Threshold %</label>
                        <Input
                          type="number"
                          min={0}
                          max={100}
                          value={newReportParams.threshold_percentage || "20"}
                          onChange={(e) => setNewReportParams({ ...newReportParams, threshold_percentage: e.target.value })}
                        />
                      </div>
                    )}
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                      Cancel
                    </Button>
                    <Button onClick={createReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                      {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                      Save Configuration
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            {isLoadingSaved ? (
              <div className="flex justify-center py-12">
                <Spinner className="h-8 w-8" />
              </div>
            ) : savedReports.length === 0 ? (
              <Card className="bg-card/50 border-border/50">
                <CardContent className="py-12 text-center">
                  <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Saved Reports</h3>
                  <p className="text-muted-foreground mb-4">Create your first report configuration to get started.</p>
                  <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                    <Plus className="h-4 w-4" />
                    Create Report Config
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedReports.map((report) => (
                  <Card key={report.report_id} className="bg-card/50 border-border/50 hover:bg-card/70 transition-colors">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {getReportTypeIcon(report.report_type)}
                          <CardTitle className="text-base">{report.report_name}</CardTitle>
                        </div>
                        <Badge className={cn("border", getReportTypeColor(report.report_type))}>
                          {report.report_type.replace("_", " ")}
                        </Badge>
                      </div>
                      {report.description && <CardDescription className="mt-2">{report.description}</CardDescription>}
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
                        <Clock className="h-3 w-3" />
                        Created {new Date(report.created_at).toLocaleDateString()}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => runSavedReport(report)}
                          disabled={runningReportId === report.report_id}
                          className="flex-1 gap-2 bg-orange-500 hover:bg-orange-600"
                        >
                          {runningReportId === report.report_id ? <Spinner className="h-3 w-3" /> : <Play className="h-3 w-3" />}
                          Run
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => openEditDialog(report)}>
                          <Edit className="h-3 w-3" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => deleteReport(report.report_id)} className="text-red-400 hover:text-red-300">
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Run Report Results */}
            {runReportData && runReportType && (
              <div className="mt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Report Results</h3>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setRunReportData(null);
                      setRunReportType(null);
                    }}
                  >
                    Clear Results
                  </Button>
                </div>
                <DownloadableReport fileName={`Report-${runReportType}`} data={runReportData as Record<string, unknown>} reportType={runReportType}>
                  <ReportDisplay reportType={runReportType} data={runReportData as Record<string, unknown>} />
                </DownloadableReport>
              </div>
            )}
          </TabsContent>

          {/* ========================================================================= */}
          {/* Sales Report Tab                                                          */}
          {/* ========================================================================= */}
          <TabsContent value="sales" className="space-y-6">
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle className="text-lg">Generate Sales Report</CardTitle>
                  {salesReport && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => saveCurrentReportAsConfig("SALES", { start_date: salesStartDate, end_date: salesEndDate, group_by: salesGroupBy })}
                      className="gap-2"
                    >
                      <BookmarkPlus className="h-4 w-4" />
                      Save as Config
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Start Date</label>
                    <Input
                      type="date"
                      value={salesStartDate}
                      max={salesEndDate || undefined}
                      onChange={(e) => setSalesStartDate(e.target.value)}
                      className="w-40"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">End Date</label>
                    <Input
                      type="date"
                      value={salesEndDate}
                      min={salesStartDate || undefined}
                      onChange={(e) => setSalesEndDate(e.target.value)}
                      className="w-40"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Group By</label>
                    <Select value={salesGroupBy} onValueChange={(v) => setSalesGroupBy(v as "day" | "week" | "month")}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="day">Day</SelectItem>
                        <SelectItem value="week">Week</SelectItem>
                        <SelectItem value="month">Month</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button onClick={generateSalesReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                    {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
                    Generate Report
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab("ai-reports");
                      handleGenerateAiReport("sales", {
                        start_date: salesStartDate,
                        end_date: salesEndDate,
                        group_by: salesGroupBy,
                      });
                    }}
                    variant="outline"
                    className="border-orange-500/40 text-orange-400 hover:bg-orange-500/10 gap-1.5"
                  >
                    <Sparkles className="h-4 w-4" />
                    Analyze with AI
                  </Button>
                </div>
              </CardContent>
            </Card>

            {salesReport && (
              <DownloadableReport fileName="Sales-Report" data={salesReport as unknown as Record<string, unknown>} reportType="SALES">
                <SalesReportDisplay data={salesReport} />
              </DownloadableReport>
            )}
          </TabsContent>

          {/* ========================================================================= */}
          {/* Inventory Report Tab                                                      */}
          {/* ========================================================================= */}
          <TabsContent value="inventory" className="space-y-6">
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Generate Inventory Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="lowStockOnly"
                      checked={inventoryLowStockOnly}
                      onChange={(e) => setInventoryLowStockOnly(e.target.checked)}
                      className="h-4 w-4 rounded border-border"
                    />
                    <label htmlFor="lowStockOnly" className="text-sm">
                      Low stock items only
                    </label>
                  </div>
                  <Button onClick={generateInventoryReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                    {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <Package className="h-4 w-4 mr-2" />}
                    Generate Report
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab("ai-reports");
                      handleGenerateAiReport("inventory", {
                        low_stock_only: inventoryLowStockOnly,
                      });
                    }}
                    variant="outline"
                    className="border-orange-500/40 text-orange-400 hover:bg-orange-500/10 gap-1.5"
                  >
                    <Sparkles className="h-4 w-4" />
                    Analyze with AI
                  </Button>
                </div>
              </CardContent>
            </Card>

            {inventoryReport && (
              <DownloadableReport fileName="Inventory-Report" data={inventoryReport as unknown as Record<string, unknown>} reportType="INVENTORY">
                <InventoryReportDisplay data={inventoryReport} />
              </DownloadableReport>
            )}
          </TabsContent>

          {/* ========================================================================= */}
          {/* Performance Report Tab                                                    */}
          {/* ========================================================================= */}
          <TabsContent value="performance" className="space-y-6">
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Generate Product Performance Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Start Date</label>
                    <Input
                      type="date"
                      value={perfStartDate}
                      max={perfEndDate || undefined}
                      onChange={(e) => setPerfStartDate(e.target.value)}
                      className="w-40"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">End Date</label>
                    <Input
                      type="date"
                      value={perfEndDate}
                      min={perfStartDate || undefined}
                      onChange={(e) => setPerfEndDate(e.target.value)}
                      className="w-40"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Top N Products</label>
                    <Input
                      type="number"
                      min={1}
                      max={100}
                      value={perfTopN}
                      onChange={(e) => setPerfTopN(parseInt(e.target.value) || 10)}
                      className="w-24"
                    />
                  </div>
                  <Button onClick={generatePerformanceReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                    {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
                    Generate Report
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab("ai-reports");
                      handleGenerateAiReport("product-performance", {
                        start_date: perfStartDate,
                        end_date: perfEndDate,
                        top_n: perfTopN,
                      });
                    }}
                    variant="outline"
                    className="border-orange-500/40 text-orange-400 hover:bg-orange-500/10 gap-1.5"
                  >
                    <Sparkles className="h-4 w-4" />
                    Analyze with AI
                  </Button>
                </div>
              </CardContent>
            </Card>

            {perfReport && (
              <DownloadableReport fileName="Product-Performance-Report" data={perfReport} reportType="PRODUCT_PERFORMANCE">
                <ProductPerformanceDisplay data={perfReport as any} />
              </DownloadableReport>
            )}
          </TabsContent>

          {/* ========================================================================= */}
          {/* Low Stock Report Tab                                                      */}
          {/* ========================================================================= */}
          <TabsContent value="lowstock" className="space-y-6">
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Generate Low Stock Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Threshold %</label>
                    <Input
                      type="number"
                      min={0}
                      max={100}
                      value={lowStockThreshold}
                      onChange={(e) => setLowStockThreshold(parseInt(e.target.value) || 20)}
                      className="w-24"
                    />
                  </div>
                  <Button onClick={generateLowStockReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                    {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <AlertTriangle className="h-4 w-4 mr-2" />}
                    Generate Report
                  </Button>
                  <Button
                    onClick={() => {
                      setActiveTab("ai-reports");
                      handleGenerateAiReport("low-stock", {
                        threshold_percentage: lowStockThreshold,
                      });
                    }}
                    variant="outline"
                    className="border-orange-500/40 text-orange-400 hover:bg-orange-500/10 gap-1.5"
                  >
                    <Sparkles className="h-4 w-4" />
                    Analyze with AI
                  </Button>
                </div>
              </CardContent>
            </Card>

            {lowStockReport && (
              <DownloadableReport fileName="Low-Stock-Report" data={lowStockReport} reportType="LOW_STOCK">
                <LowStockReportDisplay data={lowStockReport as any} />
              </DownloadableReport>
            )}
          </TabsContent>
        </Tabs>

        {/* Edit Report Dialog */}
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Edit Report Configuration</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Report Name *</label>
                <Input
                  value={newReportName}
                  onChange={(e) => setNewReportName(e.target.value)}
                  placeholder="e.g., Monthly Sales Report"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Description</label>
                <Textarea
                  value={newReportDescription}
                  onChange={(e) => setNewReportDescription(e.target.value)}
                  placeholder="Optional description..."
                  rows={2}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowEditDialog(false);
                  setEditingReport(null);
                  resetNewReportForm();
                }}
              >
                Cancel
              </Button>
              <Button onClick={updateReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                Update
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
}
