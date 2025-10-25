"""Physics curriculum mapping: chapters → topics.

Use this to constrain model generation so it selects a chapter and one or
more topics from the allowed lists instead of inventing arbitrary labels.

Example usage in a prompt (YAML header in generated TeX):

% chapter: Rotational Motion
% topics: [Angular momentum, Torque]

Helpers:
- `format_for_prompt()` → textual list for inclusion in prompts
- `validate_selection(chapter, topics)` → returns (ok, missing)
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

CURRICULUM: Dict[str, List[str]] = {
    "Physics and Measurement": [
        "Units of measurement",
        "System of units",
        "SI units",
        "Fundamental units",
        "Derived units",
        "Least count",
        "Significant figures",
        "Errors in measurement",
        "Dimensions of physical quantities",
        "Dimensional analysis"
    ],

    "Kinematics": [
        "Frame of reference",
        "Motion in a straight line",
        "Position–time graph",
        "Speed",
        "Average speed",
        "Instantaneous speed",
        "Velocity",
        "Average velocity",
        "Instantaneous velocity",
        "Uniform motion",
        "Non-uniform motion",
        "Uniformly accelerated motion",
        "Velocity–time graph",
        "Relations for uniformly accelerated motion",
        "Scalars and vectors",
        "Vector addition",
        "Vector subtraction",
        "Scalar product",
        "Vector product",
        "Unit vector",
        "Resolution of a vector",
        "Relative velocity",
        "Motion in a plane",
        "Projectile motion",
        "Uniform circular motion"
    ],

    "Laws of Motion": [
        "Force and inertia",
        "Newton’s first law",
        "Momentum",
        "Newton’s second law",
        "Impulse",
        "Newton’s third law",
        "Conservation of linear momentum",
        "Equilibrium of concurrent forces",
        "Static friction",
        "Kinetic friction",
        "Laws of friction",
        "Rolling friction",
        "Dynamics of uniform circular motion",
        "Centripetal force",
        "Vehicle on a level circular road",
        "Vehicle on a banked road"
    ],

    "Work, Energy and Power": [
        "Work done by a constant force",
        "Work done by a variable force",
        "Kinetic energy",
        "Potential energy",
        "Work–energy theorem",
        "Power",
        "Potential energy of a spring",
        "Conservation of mechanical energy",
        "Conservative forces",
        "Non-conservative forces",
        "Motion in a vertical circle",
        "Elastic collisions in one dimension",
        "Inelastic collisions in one dimension",
        "Collisions in two dimensions"
    ],

    "Rotational Motion": [
        "Centre of mass of a two-particle system",
        "Centre of mass of a rigid body",
        "Basic concepts of rotational motion",
        "Moment of a force",
        "Torque",
        "Angular momentum",
        "Conservation of angular momentum",
        "Moment of inertia",
        "Radius of gyration",
        "Moments of inertia for simple geometrical objects",
        "Parallel axis theorem",
        "Perpendicular axis theorem",
        "Equilibrium of rigid bodies",
        "Rigid-body rotation",
        "Comparison of linear and rotational motion"
    ],

    "Gravitation": [
        "Universal law of gravitation",
        "Acceleration due to gravity",
        "Variation of g with altitude",
        "Variation of g with depth",
        "Kepler’s laws of planetary motion",
        "Gravitational potential energy",
        "Gravitational potential",
        "Escape velocity",
        "Motion of a satellite",
        "Orbital velocity",
        "Time period of a satellite",
        "Energy of a satellite"
    ],

    "Properties of Solids and Liquids": [
        "Elastic behaviour",
        "Stress–strain relationship",
        "Hooke’s law",
        "Young’s modulus",
        "Bulk modulus",
        "Modulus of rigidity",
        "Pressure due to a fluid column",
        "Pascal’s law",
        "Effect of gravity on fluid pressure",
        "Viscosity",
        "Stokes’ law",
        "Terminal velocity",
        "Streamline flow",
        "Turbulent flow",
        "Critical velocity",
        "Bernoulli’s principle",
        "Surface energy",
        "Surface tension",
        "Angle of contact",
        "Excess pressure across a curved surface",
        "Drops and bubbles",
        "Capillary rise",
        "Heat and temperature",
        "Thermal expansion",
        "Specific heat capacity",
        "Calorimetry",
        "Change of state",
        "Latent heat",
        "Heat conduction",
        "Convection",
        "Radiation"
    ],

    "Thermodynamics": [
        "Thermal equilibrium",
        "Zeroth law of thermodynamics",
        "Concept of temperature",
        "Heat",
        "Work",
        "Internal energy",
        "First law of thermodynamics",
        "Isothermal process",
        "Adiabatic process",
        "Second law of thermodynamics",
        "Reversible processes",
        "Irreversible processes"
    ],

    "Kinetic Theory of Gases": [
        "Equation of state of a perfect gas",
        "Work done on compressing a gas",
        "Assumptions of kinetic theory",
        "Pressure of gas",
        "Kinetic interpretation of temperature",
        "RMS speed of gas molecules",
        "Degrees of freedom",
        "Law of equipartition of energy",
        "Specific heat capacities of gases",
        "Mean free path",
        "Avogadro’s number"
    ],

    "Oscillations and Waves": [
        "Oscillations",
        "Periodic motion",
        "Time period",
        "Frequency",
        "Displacement–time relation",
        "Simple harmonic motion",
        "Phase",
        "Oscillations of a spring",
        "Restoring force",
        "Force constant",
        "Energy in SHM",
        "Simple pendulum",
        "Wave motion",
        "Longitudinal waves",
        "Transverse waves",
        "Speed of a wave",
        "Progressive wave equation",
        "Superposition principle",
        "Reflection of waves",
        "Standing waves in strings",
        "Standing waves in organ pipes",
        "Fundamental mode",
        "Harmonics",
        "Beats"
    ],

    "Electrostatics": [
        "Electric charge",
        "Conservation of charge",
        "Coulomb’s law",
        "Superposition principle",
        "Continuous charge distribution",
        "Electric field",
        "Electric field lines",
        "Electric field due to a point charge",
        "Electric dipole",
        "Torque on a dipole",
        "Electric flux",
        "Gauss’s law",
        "Field due to a long wire",
        "Field due to an infinite plane sheet",
        "Field due to a thin spherical shell",
        "Electric potential",
        "Potential due to a point charge",
        "Potential due to a dipole",
        "Equipotential surfaces",
        "Potential energy of two charges",
        "Potential energy of a dipole",
        "Conductors and insulators",
        "Dielectrics and polarization",
        "Capacitor",
        "Capacitance",
        "Capacitors in series",
        "Capacitors in parallel",
        "Parallel-plate capacitor with dielectric",
        "Energy stored in a capacitor"
    ],

    "Current Electricity": [
        "Electric current",
        "Drift velocity",
        "Mobility",
        "Relation between drift velocity and current",
        "Ohm’s law",
        "Resistance",
        "I–V characteristics of Ohmic conductors",
        "I–V characteristics of non-Ohmic conductors",
        "Resistivity",
        "Conductivity",
        "Series combination of resistors",
        "Parallel combination of resistors",
        "Temperature dependence of resistance",
        "Internal resistance",
        "Emf of a cell",
        "Potential difference",
        "Cells in series",
        "Cells in parallel",
        "Kirchhoff’s laws",
        "Wheatstone bridge",
        "Metre bridge",
        "Electrical energy",
        "Electrical power"
    ],

    "Magnetic Effects of Current and Magnetism": [
        "Biot–Savart law",
        "Magnetic field due to a circular loop",
        "Ampere’s law",
        "Magnetic field due to a straight wire",
        "Magnetic field due to a solenoid",
        "Force on a moving charge",
        "Force on a current-carrying conductor",
        "Force between parallel current-carrying conductors",
        "Definition of ampere",
        "Torque on a current loop",
        "Moving-coil galvanometer",
        "Conversion of galvanometer to ammeter",
        "Conversion of galvanometer to voltmeter",
        "Current loop as a magnetic dipole",
        "Magnetic dipole moment",
        "Bar magnet as an equivalent solenoid",
        "Magnetic field lines",
        "Magnetic field of a bar magnet (axial and equatorial)",
        "Torque on a magnetic dipole",
        "Paramagnetic substances",
        "Diamagnetic substances",
        "Ferromagnetic substances",
        "Temperature effect on magnetic properties"
    ],

    "Electromagnetic Induction and Alternating Currents": [
        "Faraday’s law",
        "Induced emf",
        "Induced current",
        "Lenz’s law",
        "Eddy currents",
        "Self inductance",
        "Mutual inductance",
        "Alternating current",
        "Peak value",
        "RMS value",
        "Reactance",
        "Impedance",
        "LCR series circuit",
        "Resonance",
        "Power in AC circuit",
        "Wattless current",
        "AC generator",
        "Transformer"
    ],

    "Electromagnetic Waves": [
        "Displacement current",
        "Electromagnetic waves",
        "Transverse nature of EM waves",
        "Electromagnetic spectrum",
        "Applications of electromagnetic waves"
    ],

    "Optics": [
        "Reflection of light",
        "Spherical mirrors",
        "Mirror formula",
        "Refraction at plane surfaces",
        "Refraction at spherical surfaces",
        "Thin lens formula",
        "Lens maker’s formula",
        "Total internal reflection",
        "Magnification",
        "Power of a lens",
        "Combination of lenses in contact",
        "Refraction through a prism",
        "Microscope",
        "Astronomical telescope",
        "Wavefront",
        "Huygens’ principle",
        "Interference of light",
        "Young’s double-slit experiment",
        "Fringe width expression",
        "Coherent sources",
        "Diffraction through single slit",
        "Width of central maximum",
        "Polarization",
        "Plane-polarized light",
        "Brewster’s law",
        "Polaroids"
    ],

    "Dual Nature of Matter and Radiation": [
        "Dual nature of radiation",
        "Photoelectric effect",
        "Hertz and Lenard’s observations",
        "Einstein’s photoelectric equation",
        "Particle nature of light",
        "Matter waves",
        "de Broglie relation"
    ],

    "Atoms and Nuclei": [
        "Alpha-particle scattering experiment",
        "Rutherford model",
        "Bohr model",
        "Energy levels of hydrogen atom",
        "Hydrogen spectrum",
        "Composition of nucleus",
        "Size of nucleus",
        "Atomic masses",
        "Mass–energy relation",
        "Mass defect",
        "Binding energy per nucleon",
        "Variation of binding energy with mass number",
        "Nuclear fission",
        "Nuclear fusion"
    ],

    "Electronic Devices": [
        "Semiconductors",
        "PN-junction diode",
        "Forward bias characteristics",
        "Reverse bias characteristics",
        "Diode as rectifier",
        "LED",
        "Photodiode",
        "Solar cell",
        "Zener diode",
        "Zener diode breakdown",
        "Zener diode as voltage regulator",
        "Logic gates",
        "OR gate",
        "AND gate",
        "NOT gate",
        "NAND gate",
        "NOR gate"
    ],

    "Experimental Skills": [
        "Vernier calipers measurement",
        "Screw gauge measurement",
        "Simple pendulum",
        "Metre scale and moments",
        "Young’s modulus of wire",
        "Surface tension by capillary rise",
        "Effect of detergents on surface tension",
        "Viscosity by terminal velocity",
        "Speed of sound using resonance tube",
        "Specific heat of solids by mixtures method",
        "Specific heat of liquids by mixtures method",
        "Resistivity using metre bridge",
        "Resistance using Ohm’s law",
        "Figure of merit of galvanometer",
        "Focal length of convex mirror",
        "Focal length of concave mirror",
        "Focal length of convex lens",
        "Angle of deviation vs incidence for prism",
        "Refractive index using travelling microscope",
        "PN-junction diode characteristics",
        "Zener diode characteristics",
        "Identification of electronic components"
    ]
}


def chapters() -> List[str]:
    return list(CURRICULUM.keys())


def topics_for(chapter: str) -> List[str]:
    return CURRICULUM.get(chapter, [])


def validate_selection(chapter: str, topics: Iterable[str]) -> Tuple[bool, List[str]]:
    """Return (is_valid, missing_topics) for the given selection.

    - Valid if `chapter` exists and all `topics` appear under that chapter.
    - Returns a list of any missing topics.
    """
    allowed = set(CURRICULUM.get(chapter, []))
    req = list(topics)
    missing = [t for t in req if t not in allowed]
    return (chapter in CURRICULUM) and (len(missing) == 0), missing


def format_for_prompt() -> str:
    """Human-readable list of chapters and topics to embed in a prompt."""
    lines: List[str] = []
    for ch, ts in CURRICULUM.items():
        lines.append(f"- Chapter: {ch}")
        for t in ts:
            lines.append(f"  - {t}")
    return "\n".join(lines)
