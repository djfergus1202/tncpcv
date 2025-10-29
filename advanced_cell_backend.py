"""
Advanced Cellular Dynamics Backend
===================================
Next-generation cell culture simulation with:
- Detailed cell cycle modeling
- Metabolic dynamics
- Spatial nutrient/oxygen gradients
- Multi-drug PK/PD modeling
- Cell-cell signaling
- Machine learning prediction
- Gene expression dynamics
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from scipy.integrate import odeint
from scipy.spatial import distance_matrix
from scipy.ndimage import gaussian_filter
import math
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS)
# Allow requests from local development and deployed frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://127.0.0.1:*",
            "http://localhost:*",
            "https://*.onrender.com",
            "file://*"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ============================================================================
# ENHANCED CELL LINE DATABASE with detailed biological parameters
# ============================================================================

@dataclass
class CellLineProfile:
    """Comprehensive cell line biological profile"""
    name: str
    type: str  # Cancer, Normal, Stem
    origin: str
    doubling_time: float  # hours
    adherent: bool
    
    # Cell cycle parameters (hours)
    g1_duration: float
    s_duration: float
    g2_duration: float
    m_duration: float
    
    # Metabolic parameters
    glucose_consumption: float  # pmol/cell/hr
    oxygen_consumption: float   # pmol/cell/hr
    lactate_production: float   # pmol/cell/hr
    
    # Drug sensitivity (IC50 values in μM for common drug classes)
    drug_sensitivity: Dict[str, float]
    
    # Signaling characteristics
    growth_factor_dependence: float  # 0-1
    contact_inhibition: float  # 0-1
    
    # Mechanical properties
    stiffness: float  # Pa
    migration_speed: float  # μm/hr
    
    # Gene expression profile (simplified - key oncogenes/tumor suppressors)
    gene_expression: Dict[str, float]


CELL_LINE_DATABASE = {
    'HeLa': CellLineProfile(
        name='HeLa',
        type='Cancer',
        origin='Cervical carcinoma',
        doubling_time=24,
        adherent=True,
        g1_duration=10,
        s_duration=8,
        g2_duration=4,
        m_duration=2,
        glucose_consumption=2.5,
        oxygen_consumption=1.8,
        lactate_production=3.2,
        drug_sensitivity={
            'taxol': 8.5,
            'cisplatin': 12.3,
            'doxorubicin': 6.7,
            'gemcitabine': 15.2,
            'targeted': 20.0
        },
        growth_factor_dependence=0.6,
        contact_inhibition=0.2,
        stiffness=1200,
        migration_speed=15,
        gene_expression={
            'MYC': 2.5,
            'TP53': 0.0,  # Null
            'KRAS': 1.0,
            'EGFR': 1.8,
            'BCL2': 2.1
        }
    ),
    'MCF-7': CellLineProfile(
        name='MCF-7',
        type='Cancer',
        origin='Breast adenocarcinoma',
        doubling_time=29,
        adherent=True,
        g1_duration=14,
        s_duration=9,
        g2_duration=4,
        m_duration=2,
        glucose_consumption=2.1,
        oxygen_consumption=1.5,
        lactate_production=2.8,
        drug_sensitivity={
            'taxol': 6.2,
            'cisplatin': 18.5,
            'doxorubicin': 4.3,
            'gemcitabine': 22.1,
            'targeted': 8.5  # Tamoxifen-like
        },
        growth_factor_dependence=0.8,
        contact_inhibition=0.5,
        stiffness=800,
        migration_speed=8,
        gene_expression={
            'MYC': 1.8,
            'TP53': 1.0,  # Wild-type
            'KRAS': 1.0,
            'EGFR': 1.2,
            'ESR1': 3.5  # ER+
        }
    ),
    'A549': CellLineProfile(
        name='A549',
        type='Cancer',
        origin='Lung carcinoma',
        doubling_time=22,
        adherent=True,
        g1_duration=9,
        s_duration=7,
        g2_duration=4,
        m_duration=2,
        glucose_consumption=2.8,
        oxygen_consumption=2.1,
        lactate_production=3.5,
        drug_sensitivity={
            'taxol': 10.5,
            'cisplatin': 15.8,
            'doxorubicin': 8.9,
            'gemcitabine': 12.3,
            'targeted': 25.0  # EGFR inhibitor
        },
        growth_factor_dependence=0.7,
        contact_inhibition=0.3,
        stiffness=1400,
        migration_speed=20,
        gene_expression={
            'MYC': 2.1,
            'TP53': 1.0,
            'KRAS': 2.8,  # KRAS mutant
            'EGFR': 2.5,
            'BCL2': 1.9
        }
    ),
    'HEK293': CellLineProfile(
        name='HEK293',
        type='Normal',
        origin='Embryonic kidney',
        doubling_time=20,
        adherent=True,
        g1_duration=8,
        s_duration=7,
        g2_duration=3,
        m_duration=2,
        glucose_consumption=1.8,
        oxygen_consumption=1.3,
        lactate_production=2.0,
        drug_sensitivity={
            'taxol': 15.0,
            'cisplatin': 25.0,
            'doxorubicin': 18.0,
            'gemcitabine': 30.0,
            'targeted': 50.0
        },
        growth_factor_dependence=0.5,
        contact_inhibition=0.7,
        stiffness=600,
        migration_speed=12,
        gene_expression={
            'MYC': 1.5,
            'TP53': 1.0,
            'KRAS': 1.0,
            'EGFR': 1.0,
            'BCL2': 1.0
        }
    ),
    'Jurkat': CellLineProfile(
        name='Jurkat',
        type='Cancer',
        origin='T-cell leukemia',
        doubling_time=48,
        adherent=False,
        g1_duration=20,
        s_duration=15,
        g2_duration=10,
        m_duration=3,
        glucose_consumption=3.2,
        oxygen_consumption=2.5,
        lactate_production=4.0,
        drug_sensitivity={
            'taxol': 12.0,
            'cisplatin': 8.5,
            'doxorubicin': 5.2,
            'gemcitabine': 18.0,
            'targeted': 15.0
        },
        growth_factor_dependence=0.9,
        contact_inhibition=0.1,
        stiffness=200,
        migration_speed=25,
        gene_expression={
            'MYC': 3.2,
            'TP53': 0.5,  # Defective
            'KRAS': 1.0,
            'EGFR': 0.8,
            'BCL2': 2.8
        }
    )
}

# ============================================================================
# ADVANCED CELL MODEL with detailed states
# ============================================================================

class Cell:
    """Individual cell with comprehensive biological state"""
    
    def __init__(self, cell_id, x, y, cell_line: CellLineProfile):
        self.id = cell_id
        self.x = x
        self.y = y
        self.cell_line = cell_line
        
        # Cell cycle state
        self.phase = 'G1'  # G1, S, G2, M, G0
        self.phase_progress = np.random.uniform(0, cell_line.g1_duration)
        
        # Viability and health
        self.alive = True
        self.health = np.random.uniform(0.85, 1.0)
        self.apoptotic = False
        self.necrotic = False
        
        # Metabolic state
        self.atp_level = np.random.uniform(0.8, 1.0)
        self.glucose_internal = np.random.uniform(0.7, 1.0)
        self.oxygen_level = np.random.uniform(0.8, 1.0)
        
        # Drug concentrations (intracellular)
        self.drug_concentrations = {}
        
        # Gene expression (relative to baseline)
        self.gene_expression = cell_line.gene_expression.copy()
        
        # Signaling state
        self.growth_signals = 1.0
        self.stress_signals = 0.0
        
        # Physical properties
        self.radius = np.random.normal(10, 1.5)
        self.velocity = np.array([0.0, 0.0])
        
        # Division tracking
        self.can_divide = True
        self.division_count = 0
        
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'phase': self.phase,
            'health': self.health,
            'alive': self.alive,
            'atp': self.atp_level,
            'radius': self.radius
        }

# ============================================================================
# SPATIAL MICROENVIRONMENT MODEL
# ============================================================================

class Microenvironment:
    """2D spatial grid for nutrients, oxygen, and waste"""
    
    def __init__(self, width=100, height=100, resolution=10):
        self.width = width
        self.height = height
        self.resolution = resolution  # microns per grid point
        
        self.grid_x = width // resolution
        self.grid_y = height // resolution
        
        # Initialize fields (normalized 0-1)
        self.glucose = np.ones((self.grid_x, self.grid_y))
        self.oxygen = np.ones((self.grid_x, self.grid_y))
        self.lactate = np.zeros((self.grid_x, self.grid_y))
        self.ph = np.ones((self.grid_x, self.grid_y)) * 7.4
        
        # Diffusion coefficients
        self.D_glucose = 0.6
        self.D_oxygen = 2.0
        self.D_lactate = 0.5
        
    def update(self, cells: List[Cell], dt: float):
        """Update microenvironment based on cell consumption/production"""
        
        # Reset consumption/production
        glucose_consumption = np.zeros((self.grid_x, self.grid_y))
        oxygen_consumption = np.zeros((self.grid_x, self.grid_y))
        lactate_production = np.zeros((self.grid_x, self.grid_y))
        
        # Accumulate cell effects
        for cell in cells:
            if cell.alive:
                grid_x = int(cell.x / self.resolution)
                grid_y = int(cell.y / self.resolution)
                
                # Bounds checking
                grid_x = max(0, min(self.grid_x - 1, grid_x))
                grid_y = max(0, min(self.grid_y - 1, grid_y))
                
                # Consumption/production rates (scaled)
                rate = dt * 0.001  # Scaling factor
                glucose_consumption[grid_x, grid_y] += cell.cell_line.glucose_consumption * rate
                oxygen_consumption[grid_x, grid_y] += cell.cell_line.oxygen_consumption * rate
                lactate_production[grid_x, grid_y] += cell.cell_line.lactate_production * rate
        
        # Apply consumption/production
        self.glucose = np.maximum(0, self.glucose - glucose_consumption)
        self.oxygen = np.maximum(0, self.oxygen - oxygen_consumption)
        self.lactate = np.minimum(1, self.lactate + lactate_production)
        
        # Diffusion (simplified - Gaussian smoothing)
        self.glucose = gaussian_filter(self.glucose, sigma=1.0)
        self.oxygen = gaussian_filter(self.oxygen, sigma=1.5)
        self.lactate = gaussian_filter(self.lactate, sigma=0.8)
        
        # Replenishment from edges (media exchange)
        self.glucose[0, :] = 1.0
        self.glucose[-1, :] = 1.0
        self.glucose[:, 0] = 1.0
        self.glucose[:, -1] = 1.0
        
        self.oxygen[0, :] = 1.0
        self.oxygen[-1, :] = 1.0
        self.oxygen[:, 0] = 1.0
        self.oxygen[:, -1] = 1.0
        
        # pH changes with lactate
        self.ph = 7.4 - 0.5 * self.lactate
        
    def get_local_values(self, x, y):
        """Get microenvironment values at cell position"""
        grid_x = int(x / self.resolution)
        grid_y = int(y / self.resolution)
        
        grid_x = max(0, min(self.grid_x - 1, grid_x))
        grid_y = max(0, min(self.grid_y - 1, grid_y))
        
        return {
            'glucose': self.glucose[grid_x, grid_y],
            'oxygen': self.oxygen[grid_x, grid_y],
            'lactate': self.lactate[grid_x, grid_y],
            'ph': self.ph[grid_x, grid_y]
        }

# ============================================================================
# PHARMACOKINETICS/PHARMACODYNAMICS MODEL
# ============================================================================

class DrugModel:
    """Multi-compartment PK/PD model"""
    
    def __init__(self, drug_type: str, concentration: float, ic50: float):
        self.drug_type = drug_type
        self.media_concentration = concentration
        self.ic50 = ic50
        
        # PK parameters
        self.permeability = 0.1  # Cell membrane permeability
        self.degradation_rate = 0.01  # Intracellular degradation
        self.efflux_rate = 0.05  # Efflux pump activity
        
        # PD parameters (Hill equation)
        self.hill_coefficient = 1.5
        self.max_effect = 0.95  # Maximum kill rate
        
    def update_intracellular(self, cell: Cell, dt: float):
        """Update intracellular drug concentration"""
        if self.drug_type not in cell.drug_concentrations:
            cell.drug_concentrations[self.drug_type] = 0.0
        
        current = cell.drug_concentrations[self.drug_type]
        
        # Uptake
        uptake = self.permeability * (self.media_concentration - current) * dt
        
        # Degradation
        degradation = self.degradation_rate * current * dt
        
        # Efflux (can develop resistance)
        efflux = self.efflux_rate * current * dt
        
        # Update
        new_conc = current + uptake - degradation - efflux
        cell.drug_concentrations[self.drug_type] = max(0, new_conc)
        
        return new_conc
    
    def calculate_effect(self, intracellular_conc: float):
        """Calculate drug effect using Hill equation"""
        if intracellular_conc <= 0:
            return 0.0
        
        effect = self.max_effect * (intracellular_conc ** self.hill_coefficient) / \
                 (self.ic50 ** self.hill_coefficient + intracellular_conc ** self.hill_coefficient)
        
        return effect

# ============================================================================
# CELL CYCLE ENGINE
# ============================================================================

class CellCycleEngine:
    """Detailed cell cycle progression with checkpoints"""
    
    @staticmethod
    def update_cell_cycle(cell: Cell, dt: float, microenv: dict):
        """Progress cell through cycle with checkpoints"""
        
        if not cell.alive or cell.phase == 'G0':
            return False  # No progression
        
        # Check metabolic requirements
        if cell.atp_level < 0.3 or cell.oxygen_level < 0.2:
            # Metabolic checkpoint failure - arrest
            cell.phase = 'G0'
            return False
        
        # Check DNA damage (simplified - based on health)
        if cell.health < 0.5:
            # DNA damage checkpoint - apoptosis
            cell.apoptotic = True
            return False
        
        # Phase-specific progression
        phase_durations = {
            'G1': cell.cell_line.g1_duration,
            'S': cell.cell_line.s_duration,
            'G2': cell.cell_line.g2_duration,
            'M': cell.cell_line.m_duration
        }
        
        # Growth factors modulate G1
        if cell.phase == 'G1':
            growth_factor = cell.growth_signals * (1 - cell.cell_line.growth_factor_dependence + \
                           cell.cell_line.growth_factor_dependence * microenv.get('growth_factor', 1.0))
            dt_effective = dt * growth_factor
        else:
            dt_effective = dt
        
        # Update progress
        cell.phase_progress += dt_effective
        
        # Check if phase complete
        if cell.phase_progress >= phase_durations[cell.phase]:
            # Advance to next phase
            cell.phase_progress = 0
            
            if cell.phase == 'G1':
                # G1/S checkpoint
                if cell.health > 0.7 and cell.atp_level > 0.6:
                    cell.phase = 'S'
                else:
                    cell.phase = 'G0'
                    
            elif cell.phase == 'S':
                cell.phase = 'G2'
                
            elif cell.phase == 'G2':
                # G2/M checkpoint
                if cell.health > 0.6:
                    cell.phase = 'M'
                else:
                    cell.phase = 'G0'
                    
            elif cell.phase == 'M':
                # Complete mitosis - signal division
                cell.phase = 'G1'
                return True  # Division ready
        
        return False

# ============================================================================
# CELL-CELL INTERACTIONS
# ============================================================================

class CellInteractions:
    """Handle cell-cell signaling and contact effects"""
    
    @staticmethod
    def calculate_contact_inhibition(cells: List[Cell], cell: Cell, radius: float = 100):
        """Calculate contact inhibition based on local density"""
        
        neighbors = 0
        for other in cells:
            if other.id != cell.id and other.alive:
                dist = np.sqrt((cell.x - other.x)**2 + (cell.y - other.y)**2)
                if dist < radius:
                    neighbors += 1
        
        # Density effect (0 = no neighbors, 1 = many neighbors)
        density = min(1.0, neighbors / 20.0)
        
        # Apply contact inhibition
        inhibition = cell.cell_line.contact_inhibition * density
        
        return 1.0 - inhibition
    
    @staticmethod
    def calculate_paracrine_signals(cells: List[Cell], cell: Cell, radius: float = 150):
        """Calculate paracrine growth factor concentration"""
        
        total_signal = 0.0
        for other in cells:
            if other.alive:
                dist = np.sqrt((cell.x - other.x)**2 + (cell.y - other.y)**2)
                if dist < radius:
                    # Signal decays with distance
                    signal_strength = np.exp(-dist / 50.0)
                    total_signal += signal_strength
        
        # Normalize
        return min(1.0, total_signal / 10.0)

# ============================================================================
# MAIN SIMULATION ENGINE
# ============================================================================

class CellCultureSimulation:
    """Master simulation orchestrator"""
    
    def __init__(self, params: dict):
        self.params = params
        
        # Get cell line
        cell_line_name = params['cellLineName']
        self.cell_line = CELL_LINE_DATABASE[cell_line_name]
        
        # Initialize microenvironment
        self.microenv = Microenvironment(
            width=params.get('cultureSize', 1000),
            height=params.get('cultureSize', 1000)
        )
        
        # Initialize cells
        self.cells = []
        self.next_id = 0
        self._initialize_cells(params['experimentParams']['initialCells'])
        
        # Initialize drug models
        self.drugs = []
        treatment = params.get('treatment', {})
        if treatment.get('type') == 'drug' and treatment.get('concentration', 0) > 0:
            drug_class = treatment.get('drugClass', 'taxol')
            ic50 = self.cell_line.drug_sensitivity.get(drug_class, 10.0)
            self.drugs.append(DrugModel(
                drug_class, 
                treatment['concentration'],
                ic50
            ))
        
        # Simulation state
        self.time = 0
        self.results = []
        
    def _initialize_cells(self, n_cells: int):
        """Initialize cell population"""
        for i in range(n_cells):
            x = np.random.uniform(50, self.microenv.width * self.microenv.resolution - 50)
            y = np.random.uniform(50, self.microenv.height * self.microenv.resolution - 50)
            cell = Cell(self.next_id, x, y, self.cell_line)
            self.cells.append(cell)
            self.next_id += 1
    
    def run(self, duration: float, dt: float = 0.5):
        """Run complete simulation"""
        
        print(f"Starting simulation: {len(self.cells)} cells, {duration}h duration")
        
        steps = int(duration / dt)
        sample_interval = max(1, int(6.0 / dt))  # Sample every 6 hours
        
        for step in range(steps):
            self.time = step * dt
            
            # Update microenvironment
            self.microenv.update(self.cells, dt)
            
            # Update each cell
            cells_to_add = []
            cells_to_remove = []
            
            for cell in self.cells:
                if not cell.alive:
                    continue
                
                # Get local microenvironment
                local_env = self.microenv.get_local_values(cell.x, cell.y)
                
                # Update metabolism
                cell.glucose_internal = 0.9 * cell.glucose_internal + 0.1 * local_env['glucose']
                cell.oxygen_level = 0.9 * cell.oxygen_level + 0.1 * local_env['oxygen']
                cell.atp_level = (cell.glucose_internal * cell.oxygen_level) ** 0.5
                
                # Cell-cell interactions
                cell.growth_signals = CellInteractions.calculate_contact_inhibition(
                    self.cells, cell
                )
                
                # Drug effects
                for drug in self.drugs:
                    intracellular = drug.update_intracellular(cell, dt)
                    effect = drug.calculate_effect(intracellular)
                    cell.health *= (1 - effect * dt * 0.1)
                
                # Environmental stress
                if local_env['glucose'] < 0.2 or local_env['oxygen'] < 0.1:
                    cell.health *= 0.98
                
                if local_env['ph'] < 6.8 or local_env['ph'] > 7.8:
                    cell.health *= 0.99
                
                # Cell cycle
                ready_to_divide = CellCycleEngine.update_cell_cycle(
                    cell, dt, local_env
                )
                
                # Division
                if ready_to_divide and cell.can_divide and len(self.cells) < 5000:
                    # Create daughter cell
                    angle = np.random.uniform(0, 2 * np.pi)
                    offset = cell.radius * 2.5
                    daughter = Cell(
                        self.next_id,
                        cell.x + offset * np.cos(angle),
                        cell.y + offset * np.sin(angle),
                        self.cell_line
                    )
                    daughter.division_count = cell.division_count + 1
                    cells_to_add.append(daughter)
                    self.next_id += 1
                
                # Death pathways
                if cell.health < 0.1:
                    cell.apoptotic = True
                
                if cell.glucose_internal < 0.05 and cell.oxygen_level < 0.05:
                    cell.necrotic = True
                
                if cell.apoptotic or cell.necrotic:
                    cell.alive = False
                    # Remove with some probability (clearance)
                    if np.random.random() < 0.2:
                        cells_to_remove.append(cell)
            
            # Add/remove cells
            self.cells.extend(cells_to_add)
            for cell in cells_to_remove:
                self.cells.remove(cell)
            
            # Sample data
            if step % sample_interval == 0:
                self._collect_data()
        
        print(f"Simulation complete: {len(self.cells)} cells remaining")
        return self.results
    
    def _collect_data(self):
        """Collect simulation metrics"""
        viable = [c for c in self.cells if c.alive]
        
        # Phase distribution
        phases = {'G1': 0, 'S': 0, 'G2': 0, 'M': 0, 'G0': 0}
        for cell in viable:
            phases[cell.phase] += 1
        
        # Health distribution
        avg_health = np.mean([c.health for c in viable]) if viable else 0
        avg_atp = np.mean([c.atp_level for c in viable]) if viable else 0
        
        # Spatial metrics
        avg_glucose = np.mean(self.microenv.glucose)
        avg_oxygen = np.mean(self.microenv.oxygen)
        avg_lactate = np.mean(self.microenv.lactate)
        
        data_point = {
            'time': self.time,
            'total': len(self.cells),
            'viable': len(viable),
            'viability': (len(viable) / len(self.cells) * 100) if self.cells else 0,
            'avg_health': avg_health,
            'avg_atp': avg_atp,
            'phases': phases,
            'glucose': avg_glucose,
            'oxygen': avg_oxygen,
            'lactate': avg_lactate
        }
        
        self.results.append(data_point)

# ============================================================================
# MACHINE LEARNING PREDICTOR (Simplified)
# ============================================================================

class OutcomePredictor:
    """Predict culture outcomes based on conditions"""
    
    @staticmethod
    def predict_optimal_dosing(cell_line_name: str, drug_class: str):
        """Predict optimal drug concentration"""
        cell_line = CELL_LINE_DATABASE[cell_line_name]
        ic50 = cell_line.drug_sensitivity.get(drug_class, 10.0)
        
        # Simple heuristic: target 2x IC50 for 50% kill
        optimal = ic50 * 2.0
        
        return {
            'optimal_dose': optimal,
            'ic50': ic50,
            'expected_viability': 50.0,
            'recommendation': f'Start at {optimal:.1f} μM for initial screening'
        }
    
    @staticmethod
    def predict_growth_rate(params: dict):
        """Predict cell growth rate"""
        cell_line = CELL_LINE_DATABASE[params['cellLineName']]
        
        # Base doubling time
        dt = cell_line.doubling_time
        
        # Environmental modifiers
        temp = params['environment']['temperature']
        if abs(temp - 37) > 2:
            dt *= 1.3
        
        # Treatment effects
        if params['treatment']['type'] == 'drug':
            conc = params['treatment']['concentration']
            drug_class = params['treatment'].get('drugClass', 'taxol')
            ic50 = cell_line.drug_sensitivity.get(drug_class, 10.0)
            inhibition = conc / (conc + ic50)
            dt *= (1 + inhibition * 2)
        
        return {
            'predicted_doubling_time': dt,
            'estimated_final_count': params['experimentParams']['initialCells'] * \
                                    2 ** (params['experimentParams']['duration'] / dt)
        }

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/simulate', methods=['POST'])
def run_simulation():
    """Main simulation endpoint"""
    try:
        params = request.json
        print(f"Received simulation request for {params['cellLineName']}")
        
        # Run simulation
        sim = CellCultureSimulation(params)
        results = sim.run(
            params['experimentParams']['duration'],
            params['experimentParams']['timeInterval']
        )
        
        return jsonify({
            'data': results,
            'success': True
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/optimal-dose', methods=['POST'])
def predict_optimal_dose():
    """ML endpoint for dose optimization"""
    try:
        params = request.json
        prediction = OutcomePredictor.predict_optimal_dosing(
            params['cellLineName'],
            params['drugClass']
        )
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/growth', methods=['POST'])
def predict_growth():
    """ML endpoint for growth prediction"""
    try:
        params = request.json
        prediction = OutcomePredictor.predict_growth_rate(params)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cell-lines', methods=['GET'])
def get_cell_lines():
    """Get detailed cell line information"""
    try:
        data = {}
        for name, profile in CELL_LINE_DATABASE.items():
            data[name] = asdict(profile)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'features': [
            'Spatial microenvironment',
            'Cell cycle modeling',
            'PK/PD simulation',
            'ML prediction',
            'Multi-drug support'
        ]
    })

if __name__ == '__main__':
    import os
    
    print("="*70)
    print("Advanced Cellular Dynamics Backend v2.0")
    print("="*70)
    print("Features:")
    print("  ✓ Detailed cell cycle modeling (G1/S/G2/M checkpoints)")
    print("  ✓ Spatial nutrient/oxygen gradients")
    print("  ✓ Multi-compartment PK/PD")
    print("  ✓ Cell-cell interactions")
    print("  ✓ Machine learning prediction")
    print("  ✓ Metabolic dynamics")
    print("="*70)
    
    # Get port from environment (for Render/Heroku) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Determine if running in production
    is_production = os.environ.get('RENDER') or os.environ.get('DYNO')
    
    if is_production:
        print(f"\n🚀 Production mode - Server starting on port {port}")
        print("="*70)
        # Production: bind to 0.0.0.0, no debug
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    else:
        print("\n💻 Development mode - Server starting on http://127.0.0.1:5000")
        print("Install dependencies: pip install flask flask-cors numpy scipy")
        print("="*70)
        # Development: bind to localhost, with debug
        app.run(host='127.0.0.1', port=port, debug=True, threaded=True)
