// components/AppLayout.tsx
import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

type Props = { userName: string; onLogout: () => void };

export default function AppLayout({ userName, onLogout }: Props) {
  return (
    <>
      <Navbar userName={userName} onLogout={onLogout} />
      <main>
        <Outlet />
      </main>
    </>
  );
}
