import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Tenants from "./pages/Tenants";
import Releases from "./pages/Releases";
import Licenses from "./pages/Licenses";
import Billing from "./pages/Billing";
import Support from "./pages/Support";

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="tenants" element={<Tenants />} />
                    <Route path="licenses" element={<Licenses />} />
                    <Route path="releases" element={<Releases />} />
                    <Route path="billing" element={<Billing />} />
                    <Route path="support" element={<Support />} />
                    <Route path="*" element={<div className="text-center py-12 text-gray-500">Page not found</div>} />
                </Route>
            </Routes>
        </Router>
    );
}

export default App;
