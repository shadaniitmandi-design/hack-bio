import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Nav from "./components/Nav";
import Landing from "./pages/Landing";
import Console from "./pages/Console";
import Pipeline from "./pages/Pipeline";
import Footer from "./components/Footer";
import BioBackground from "./components/BioBackground";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <div className="App grain">
      <BioBackground />
      <BrowserRouter>
        <Nav />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/predict" element={<Console />} />
          <Route path="/pipeline" element={<Pipeline />} />
        </Routes>
        <Footer />
        <Toaster theme="dark" position="bottom-right" />
      </BrowserRouter>
    </div>
  );
}

export default App;
