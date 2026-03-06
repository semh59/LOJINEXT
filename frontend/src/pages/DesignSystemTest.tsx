import { useState } from 'react'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table'
import { useNotify } from '../context/NotificationContext'
import { VehicleStatusCard } from '../components/vehicles/VehicleStatusCard'

export default function DesignSystemTest() {
    const [isModalOpen, setIsModalOpen] = useState(false)
    const { notify } = useNotify()

    return (
        <div className="min-h-screen p-8 space-y-12">
            <div className="space-y-4">
                <h1 className="text-3xl font-bold">Design System Test</h1>
                <p className="text-neutral-500">Kitchen sink for checking component styles and behavior.</p>
            </div>

            {/* Buttons */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Buttons</h2>
                <div className="flex flex-wrap gap-4">
                    <Button variant="primary">Primary</Button>
                    <Button variant="secondary">Secondary</Button>
                    <Button variant="danger">Danger</Button>
                    <Button variant="ghost">Ghost</Button>
                    <Button variant="primary" isLoading>Loading</Button>
                    <Button variant="primary" disabled>Disabled</Button>
                </div>
                <div className="flex flex-wrap gap-4 items-center">
                    <Button size="sm">Small</Button>
                    <Button size="md">Medium</Button>
                    <Button size="lg">Large</Button>
                </div>
            </section>

            {/* Inputs */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Inputs</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <Input placeholder="Default input" />
                    <Input placeholder="Error input" error />
                    <Input placeholder="Disabled input" disabled />
                </div>
            </section>

            {/* Badges */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Badges</h2>
                <div className="flex gap-4">
                    <Badge variant="default">Default</Badge>
                    <Badge variant="success">Success</Badge>
                    <Badge variant="warning">Warning</Badge>
                    <Badge variant="error">Error</Badge>
                </div>
            </section>

            {/* Cards */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Cards</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Card>Default Card (Premium Glass)</Card>
                    <Card padding="lg">Large Padding</Card>
                    <Card padding="sm">Small Padding</Card>
                </div>
            </section>

            {/* Toast */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Toasts</h2>
                <div className="flex gap-4">
                    <Button onClick={() => notify('success', 'Success', 'Operation completed successfully')}>Success</Button>
                    <Button variant="danger" onClick={() => notify('error', 'Error', 'Something went wrong')}>Error</Button>
                    <Button variant="secondary" onClick={() => notify('warning', 'Warning', 'Check your settings')}>Warning</Button>
                    <Button variant="ghost" onClick={() => notify('info', 'Info', 'Did you know?')}>Info</Button>
                </div>
            </section>

            {/* Modal */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Modal</h2>
                <Button onClick={() => setIsModalOpen(true)}>Open Modal</Button>
                <Modal
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    title="Example Modal"
                >
                    <div className="space-y-4">
                        <p>This is a modal dialog content. It has a backdrop blur and smooth animation.</p>
                        <div className="flex justify-end gap-2">
                            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
                            <Button onClick={() => setIsModalOpen(false)}>Confirm</Button>
                        </div>
                    </div>
                </Modal>
            </section>

            {/* Sovereign Components (v3.2) */}
            <section className="space-y-6">
                <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-black tracking-tight text-white bg-indigo-600 px-4 py-1 rounded-xl">Sovereign Components</h2>
                    <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">v3.2 Edition</span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <VehicleStatusCard 
                        plate="34 SOV 032" 
                        model="Mercedes-Benz Actros" 
                        fuelLevel={82} 
                        tirePressure={98} 
                        engineTemp={85} 
                        status="active" 
                    />
                    <VehicleStatusCard 
                        plate="06 AGT 101" 
                        model="Ford F-Max" 
                        fuelLevel={18} 
                        tirePressure={92} 
                        engineTemp={92} 
                        status="warning" 
                    />
                    <VehicleStatusCard 
                        plate="35 MCP 999" 
                        model="Volvo FH16" 
                        fuelLevel={45} 
                        tirePressure={72} 
                        engineTemp={112} 
                        status="critical" 
                    />
                </div>
            </section>

            {/* Table */}
            <section className="space-y-4">
                <h2 className="text-xl font-semibold">Table</h2>
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>#</TableHead>
                            <TableHead>User</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Role</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        <TableRow>
                            <TableCell>1</TableCell>
                            <TableCell>John Doe</TableCell>
                            <TableCell><Badge variant="success">Active</Badge></TableCell>
                            <TableCell>Admin</TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>2</TableCell>
                            <TableCell>Jane Smith</TableCell>
                            <TableCell><Badge variant="warning">Pending</Badge></TableCell>
                            <TableCell>User</TableCell>
                        </TableRow>
                    </TableBody>
                </Table>
            </section>
        </div>
    )
}
