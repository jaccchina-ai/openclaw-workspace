#!/usr/bin/env python3
"""
遗传因子进化模块 (genetic_factor_evolution.py)
实现基于遗传算法的因子进化，通过数学表达式组合现有因子生成新的Alpha因子

主要功能:
1. 因子基因表示: 使用数学表达式表示因子 (如 "macd_dif + kdj_k * 0.5")
2. 变异操作: 改变运算符、添加/删除项、改变常数值、交换因子
3. 交叉操作: 单点交叉和均匀交叉组合父代因子
4. 适应度函数: 基于IC值 (信息系数) 评估因子有效性
5. 进化循环: 锦标赛选择、精英保留策略
"""

import random
import numpy as np
import pandas as pd
import re
import logging
from typing import List, Dict, Tuple, Optional, Any, Set
from dataclasses import dataclass, field
from copy import deepcopy

from factor_mining import Factor, FactorCategory

logger = logging.getLogger(__name__)


@dataclass
class FactorGene:
    """
    因子基因类 - 表示一个进化中的因子
    
    Attributes:
        name: 基因名称
        formula: 数学表达式公式
        factors: 使用的因子列表
        constants: 常数列表
        operators: 运算符列表 (+, -, *, /)
        fitness: 适应度值 (基于IC)
        ic_value: 信息系数值
        generation: 诞生的代数
    """
    name: str
    formula: str
    factors: List[str] = field(default_factory=list)
    constants: List[float] = field(default_factory=list)
    operators: List[str] = field(default_factory=list)
    fitness: float = 0.0
    ic_value: Optional[float] = None
    generation: int = 0
    
    @classmethod
    def from_formula(cls, name: str, formula: str, generation: int = 0) -> 'FactorGene':
        """从公式字符串创建FactorGene"""
        factors = []
        constants = []
        operators = []
        
        # 解析因子 (假设因子名是小写字母+下划线)
        factor_pattern = r'\b[a-z][a-z0-9_]*\b'
        all_identifiers = re.findall(factor_pattern, formula)
        
        # 排除数学函数和常数
        math_functions = {'sin', 'cos', 'tan', 'exp', 'log', 'sqrt', 'abs', 'sign'}
        for identifier in all_identifiers:
            if identifier not in math_functions:
                factors.append(identifier)
        
        # 解析常数 (数字)
        constant_pattern = r'\b\d+\.?\d*\b'
        constant_strs = re.findall(constant_pattern, formula)
        constants = [float(c) for c in constant_strs]
        
        # 解析运算符
        operator_pattern = r'[\+\-\*\/]'
        operators = re.findall(operator_pattern, formula)
        
        return cls(
            name=name,
            formula=formula,
            factors=list(dict.fromkeys(factors)),  # 去重但保持顺序
            constants=constants,
            operators=operators,
            generation=generation
        )
    
    def to_factor(self) -> Factor:
        """将基因转换为Factor对象"""
        return Factor(
            name=self.name.upper(),
            code=self.name.lower(),
            category=FactorCategory.CUSTOM,
            description=f"遗传进化因子 (Gen{self.generation}): {self.formula}",
            formula=self.formula,
            ic_value=self.ic_value,
            is_valid=self.ic_value is not None and abs(self.ic_value) >= 0.03,
            weight=1.0
        )
    
    def clone(self) -> 'FactorGene':
        """创建基因的深拷贝"""
        return FactorGene(
            name=self.name,
            formula=self.formula,
            factors=self.factors.copy(),
            constants=self.constants.copy(),
            operators=self.operators.copy(),
            fitness=self.fitness,
            ic_value=self.ic_value,
            generation=self.generation
        )
    
    def __hash__(self):
        return hash(self.formula)
    
    def __eq__(self, other):
        if not isinstance(other, FactorGene):
            return False
        return self.formula == other.formula


class MutationOperator:
    """变异操作类 - 实现多种变异算子"""
    
    OPERATORS = ['+', '-', '*', '/']
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
    
    def change_operator(self, gene: FactorGene, seed: Optional[int] = None) -> FactorGene:
        """改变一个运算符"""
        if seed is not None:
            random.seed(seed)
        
        if not gene.operators:
            return gene.clone()
        
        mutated = gene.clone()
        idx = random.randint(0, len(mutated.operators) - 1)
        current_op = mutated.operators[idx]
        new_op = random.choice([op for op in self.OPERATORS if op != current_op])
        mutated.operators[idx] = new_op
        mutated.formula = self._rebuild_formula(mutated)
        return mutated
    
    def add_term(self, gene: FactorGene, available_factors: List[str], 
                 seed: Optional[int] = None) -> FactorGene:
        """添加一个新项到公式"""
        if seed is not None:
            random.seed(seed)
        
        if not available_factors:
            return gene.clone()
        
        mutated = gene.clone()
        new_factor = random.choice(available_factors)
        new_op = random.choice(self.OPERATORS)
        new_constant = round(random.uniform(0.1, 2.0), 2)
        
        if random.random() < 0.5:
            new_term = f"{new_factor} * {new_constant}"
            mutated.constants.append(new_constant)
        else:
            new_term = new_factor
        
        mutated.factors.append(new_factor)
        mutated.operators.append(new_op)
        mutated.formula = f"{mutated.formula} {new_op} {new_term}"
        return mutated
    
    def remove_term(self, gene: FactorGene, seed: Optional[int] = None) -> FactorGene:
        """从公式中删除一个项"""
        if seed is not None:
            random.seed(seed)
        
        if len(gene.factors) <= 1:
            return gene.clone()
        
        mutated = gene.clone()
        
        if len(mutated.operators) == 1:
            mutated.factors = [mutated.factors[0]]
            mutated.operators = []
            mutated.formula = mutated.factors[0]
        else:
            idx = random.randint(1, len(mutated.factors) - 1)
            mutated.factors.pop(idx)
            if idx <= len(mutated.operators):
                mutated.operators.pop(min(idx - 1, len(mutated.operators) - 1))
            mutated.formula = self._rebuild_formula(mutated)
        
        return mutated
    
    def change_constant(self, gene: FactorGene, seed: Optional[int] = None) -> FactorGene:
        """改变一个常数值"""
        if seed is not None:
            random.seed(seed)
        
        if not gene.constants:
            return gene.clone()
        
        mutated = gene.clone()
        idx = random.randint(0, len(mutated.constants) - 1)
        current_val = mutated.constants[idx]
        variation = random.uniform(0.5, 1.5)
        new_val = round(current_val * variation, 2)
        if abs(new_val) < 0.01:
            new_val = 0.1
        mutated.constants[idx] = new_val
        mutated.formula = self._rebuild_formula(mutated)
        return mutated
    
    def swap_factors(self, gene: FactorGene, seed: Optional[int] = None) -> FactorGene:
        """交换两个因子的位置"""
        if seed is not None:
            random.seed(seed)
        
        if len(gene.factors) < 2:
            return gene.clone()
        
        mutated = gene.clone()
        idx1, idx2 = random.sample(range(len(mutated.factors)), 2)
        mutated.factors[idx1], mutated.factors[idx2] = mutated.factors[idx2], mutated.factors[idx1]
        mutated.formula = self._rebuild_formula(mutated)
        return mutated
    
    def mutate(self, gene: FactorGene, available_factors: List[str],
               mutation_type: Optional[str] = None, seed: Optional[int] = None) -> FactorGene:
        """执行随机变异"""
        if seed is not None:
            random.seed(seed)
        
        mutation_methods = {
            'change_operator': lambda g: self.change_operator(g),
            'add_term': lambda g: self.add_term(g, available_factors),
            'remove_term': lambda g: self.remove_term(g),
            'change_constant': lambda g: self.change_constant(g),
            'swap_factors': lambda g: self.swap_factors(g)
        }
        
        if mutation_type is None:
            mutation_type = random.choice(list(mutation_methods.keys()))
        
        if mutation_type in mutation_methods:
            return mutation_methods[mutation_type](gene)
        return gene.clone()
    
    def _rebuild_formula(self, gene: FactorGene) -> str:
        """根据基因组件重建公式"""
        if not gene.factors:
            return "0"
        if len(gene.factors) == 1:
            return gene.factors[0]
        
        parts = [gene.factors[0]]
        const_idx = 0
        
        for i in range(1, len(gene.factors)):
            if i - 1 < len(gene.operators):
                op = gene.operators[i - 1]
                factor = gene.factors[i]
                if random.random() < 0.5 and const_idx < len(gene.constants):
                    const = gene.constants[const_idx]
                    parts.append(f"{op} {factor} * {const}")
                    const_idx += 1
                else:
                    parts.append(f"{op} {factor}")
        return " ".join(parts)


class CrossoverOperator:
    """交叉操作类 - 实现多种交叉算子"""
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
    
    def single_point(self, parent1: FactorGene, parent2: FactorGene,
                     seed: Optional[int] = None) -> Tuple[FactorGene, FactorGene]:
        """单点交叉"""
        if seed is not None:
            random.seed(seed)
        
        child1 = parent1.clone()
        child2 = parent2.clone()
        
        if len(parent1.factors) > 1 and len(parent2.factors) > 1:
            point1 = random.randint(1, len(parent1.factors) - 1)
            point2 = random.randint(1, len(parent2.factors) - 1)
            
            child1.factors = parent1.factors[:point1] + parent2.factors[point2:]
            child2.factors = parent2.factors[:point2] + parent1.factors[point1:]
            child1.operators = parent1.operators[:point1-1] + parent2.operators[point2-1:]
            child2.operators = parent2.operators[:point2-1] + parent1.operators[point1-1:]
            child1.constants = parent1.constants[:point1] + parent2.constants[point2:]
            child2.constants = parent2.constants[:point2] + parent1.constants[point1:]
        
        child1.formula = self._rebuild_formula(child1)
        child2.formula = self._rebuild_formula(child2)
        child1.name = f"evolved_{random.randint(1000, 9999)}"
        child2.name = f"evolved_{random.randint(1000, 9999)}"
        return child1, child2
    
    def uniform(self, parent1: FactorGene, parent2: FactorGene,
                seed: Optional[int] = None) -> Tuple[FactorGene, FactorGene]:
        """均匀交叉"""
        if seed is not None:
            random.seed(seed)
        
        child1 = FactorGene(name=f"evolved_{random.randint(1000, 9999)}", formula="")
        child2 = FactorGene(name=f"evolved_{random.randint(1000, 9999)}", formula="")
        
        all_factors = list(set(parent1.factors + parent2.factors))
        
        for factor in all_factors:
            if random.random() < 0.5:
                if factor in parent1.factors:
                    child1.factors.append(factor)
                if factor in parent2.factors:
                    child2.factors.append(factor)
            else:
                if factor in parent2.factors:
                    child1.factors.append(factor)
                if factor in parent1.factors:
                    child2.factors.append(factor)
        
        if not child1.factors:
            child1.factors = [random.choice(parent1.factors)]
        if not child2.factors:
            child2.factors = [random.choice(parent2.factors)]
        
        for child in [child1, child2]:
            child.operators = [random.choice(['+', '-', '*', '/']) 
                              for _ in range(max(0, len(child.factors) - 1))]
            child.constants = [round(random.uniform(0.1, 2.0), 2) 
                              for _ in range(len(child.factors))]
            child.formula = self._rebuild_formula(child)
        return child1, child2
    
    def _rebuild_formula(self, gene: FactorGene) -> str:
        """重建公式"""
        if not gene.factors:
            return "0"
        if len(gene.factors) == 1:
            return gene.factors[0]
        
        parts = [gene.factors[0]]
        for i in range(1, len(gene.factors)):
            if i - 1 < len(gene.operators):
                parts.append(f"{gene.operators[i-1]} {gene.factors[i]}")
            else:
                parts.append(f"+ {gene.factors[i]}")
        return " ".join(parts)


class SelectionMethod:
    """选择方法类 - 实现多种选择策略"""
    
    def tournament(self, population: List[FactorGene], tournament_size: int,
                   num_selected: int, seed: Optional[int] = None) -> List[FactorGene]:
        """锦标赛选择"""
        if seed is not None:
            random.seed(seed)
        
        selected = []
        population_copy = population.copy()
        
        for _ in range(num_selected):
            tournament = random.sample(population_copy, 
                                      min(tournament_size, len(population_copy)))
            winner = max(tournament, key=lambda g: g.fitness)
            selected.append(winner.clone())
        return selected
    
    def elitism(self, population: List[FactorGene], elite_size: int) -> List[FactorGene]:
        """精英选择"""
        sorted_pop = sorted(population, key=lambda g: g.fitness, reverse=True)
        return [g.clone() for g in sorted_pop[:elite_size]]
    
    def roulette_wheel(self, population: List[FactorGene], 
                       num_selected: int, seed: Optional[int] = None) -> List[FactorGene]:
        """轮盘赌选择"""
        if seed is not None:
            random.seed(seed)
        
        fitnesses = [max(0, g.fitness) for g in population]
        total_fitness = sum(fitnesses)
        
        if total_fitness == 0:
            return [random.choice(population).clone() for _ in range(num_selected)]
        
        selected = []
        for _ in range(num_selected):
            pick = random.uniform(0, total_fitness)
            current = 0
            for gene, fitness in zip(population, fitnesses):
                current += fitness
                if current >= pick:
                    selected.append(gene.clone())
                    break
        return selected


class GeneticFactorEvolution:
    """遗传因子进化主类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化遗传因子进化器"""
        self.config = config or {}
        
        self.population_size = self.config.get('population_size', 50)
        self.generations = self.config.get('generations', 30)
        self.mutation_rate = self.config.get('mutation_rate', 0.3)
        self.crossover_rate = self.config.get('crossover_rate', 0.7)
        self.elitism_rate = self.config.get('elitism_rate', 0.1)
        self.tournament_size = self.config.get('tournament_size', 3)
        self.target_ic = self.config.get('target_ic', 0.05)
        
        self._validate_config()
        
        self.mutator = MutationOperator()
        self.crossover = CrossoverOperator()
        self.selector = SelectionMethod()
        
        self.population: List[FactorGene] = []
        self.best_gene: Optional[FactorGene] = None
        self.evolution_history: List[Dict[str, Any]] = []
        
        logger.info(f"遗传因子进化器初始化完成: pop={self.population_size}, "
                   f"gen={self.generations}, mut={self.mutation_rate}, "
                   f"cross={self.crossover_rate}")
    
    def _validate_config(self):
        """验证配置参数"""
        if not (0 <= self.mutation_rate <= 1):
            raise ValueError(f"变异率必须在0-1之间: {self.mutation_rate}")
        if not (0 <= self.crossover_rate <= 1):
            raise ValueError(f"交叉率必须在0-1之间: {self.crossover_rate}")
        if not (0 <= self.elitism_rate <= 1):
            raise ValueError(f"精英率必须在0-1之间: {self.elitism_rate}")
        if self.population_size < 10:
            raise ValueError(f"种群大小至少为10: {self.population_size}")
        if self.generations < 1:
            raise ValueError(f"代数至少为1: {self.generations}")
    
    def initialize_population(self, base_factors: List[str],
                              seed: Optional[int] = None) -> List[FactorGene]:
        """初始化种群"""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        population = []
        for i in range(self.population_size):
            num_factors = random.randint(2, min(4, len(base_factors)))
            selected_factors = random.sample(base_factors, num_factors)
            
            if num_factors == 1:
                formula = selected_factors[0]
            else:
                parts = [selected_factors[0]]
                for j in range(1, num_factors):
                    op = random.choice(['+', '-', '*'])
                    if random.random() < 0.5:
                        const = round(random.uniform(0.1, 2.0), 2)
                        parts.append(f"{op} {selected_factors[j]} * {const}")
                    else:
                        parts.append(f"{op} {selected_factors[j]}")
                formula = " ".join(parts)
            
            gene = FactorGene.from_formula(f"evolved_{i:04d}", formula, generation=0)
            population.append(gene)
        
        self.population = population
        logger.info(f"种群初始化完成: {len(population)} 个个体")
        return population
    
    def calculate_fitness(self, gene: FactorGene, 
                          factor_data: Optional[pd.DataFrame] = None) -> float:
        """计算基因适应度 (基于IC值)"""
        if gene.ic_value is not None:
            fitness = abs(gene.ic_value)
            if fitness >= self.target_ic:
                fitness *= 1.5
            return fitness
        
        if factor_data is None or factor_data.empty:
            complexity = len(gene.factors) + len(gene.operators)
            base_fitness = random.uniform(0.01, 0.1)
            return base_fitness * (1 + complexity * 0.05)
        
        try:
            factor_values = self._evaluate_formula(gene, factor_data)
            if factor_values is None or len(factor_values) < 10:
                gene.fitness = 0.0
                return 0.0
            
            forward_returns = factor_data['forward_return']
            mask = factor_values.notna() & forward_returns.notna()
            f = factor_values[mask]
            r = forward_returns[mask]
            
            if len(f) < 10:
                gene.fitness = 0.0
                return 0.0
            
            ic = f.corr(r, method='spearman')
            if pd.isna(ic):
                gene.ic_value = 0.0
                gene.fitness = 0.0
            else:
                gene.ic_value = float(ic)
                gene.fitness = abs(ic)
                if gene.fitness >= self.target_ic:
                    gene.fitness *= 1.5
            return gene.fitness
        except Exception as e:
            logger.warning(f"计算适应度失败: {e}")
            gene.fitness = 0.0
            return 0.0
    
    def _evaluate_formula(self, gene: FactorGene, 
                          factor_data: pd.DataFrame) -> Optional[pd.Series]:
        """评估公式并计算因子值"""
        try:
            for factor in gene.factors:
                if factor not in factor_data.columns:
                    return None
            result = factor_data.eval(gene.formula)
            return result
        except Exception as e:
            logger.debug(f"公式评估失败 '{gene.formula}': {e}")
            return None
    
    def evolve(self, base_factors: List[str],
               factor_data: Optional[pd.DataFrame] = None,
               seed: Optional[int] = None) -> Dict[str, Any]:
        """执行进化"""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        logger.info(f"开始进化: {self.generations} 代, 种群大小 {self.population_size}")
        
        self.initialize_population(base_factors, seed)
        self.evolution_history = []
        
        for generation in range(self.generations):
            for gene in self.population:
                if gene.fitness == 0.0:
                    self.calculate_fitness(gene, factor_data)
            
            fitnesses = [g.fitness for g in self.population]
            best_fitness = max(fitnesses)
            avg_fitness = sum(fitnesses) / len(fitnesses)
            
            self.evolution_history.append({
                'generation': generation,
                'best_fitness': best_fitness,
                'avg_fitness': avg_fitness,
                'best_ic': max([g.ic_value for g in self.population if g.ic_value is not None], default=0.0)
            })
            
            current_best = max(self.population, key=lambda g: g.fitness)
            if self.best_gene is None or current_best.fitness > self.best_gene.fitness:
                self.best_gene = current_best.clone()
                self.best_gene.generation = generation
            
            if self.best_gene.ic_value is not None and abs(self.best_gene.ic_value) >= self.target_ic:
                logger.info(f"第 {generation} 代达到目标IC: {self.best_gene.ic_value:.4f}")
                if generation >= 10:
                    break
            
            elite_size = max(1, int(self.population_size * self.elitism_rate))
            elites = self.selector.elitism(self.population, elite_size)
            
            new_population = elites.copy()
            
            while len(new_population) < self.population_size:
                parents = self.selector.tournament(self.population, self.tournament_size, 2)
                if len(parents) < 2:
                    parents = [random.choice(self.population), random.choice(self.population)]
                parent1, parent2 = parents[0], parents[1]
                
                if random.random() < self.crossover_rate:
                    child1, child2 = self.crossover.single_point(parent1, parent2)
                else:
                    child1, child2 = parent1.clone(), parent2.clone()
                
                for child in [child1, child2]:
                    if random.random() < self.mutation_rate:
                        mutation_type = random.choice([
                            'change_operator', 'add_term', 'remove_term',
                            'change_constant', 'swap_factors'
                        ])
                        child = self.mutator.mutate(child, base_factors, mutation_type)
                    child.generation = generation + 1
                
                new_population.extend([child1, child2])
            
            self.population = new_population[:self.population_size]
            
            if (generation + 1) % 5 == 0:
                logger.info(f"第 {generation + 1} 代完成: 最佳适应度={best_fitness:.4f}, "
                           f"平均适应度={avg_fitness:.4f}")
        
        for gene in self.population:
            if gene.fitness == 0.0:
                self.calculate_fitness(gene, factor_data)
        
        return {
            'best_gene': self.best_gene,
            'best_fitness': self.best_gene.fitness if self.best_gene else 0.0,
            'best_ic': self.best_gene.ic_value if self.best_gene else 0.0,
            'evolution_history': self.evolution_history,
            'final_population': self.population,
            'generations_completed': len(self.evolution_history)
        }
    
    def get_best_factors(self, n: int = 5) -> List[Factor]:
        """获取最佳因子"""
        if not self.population:
            return []
        
        sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
        factors = []
        for i, gene in enumerate(sorted_pop[:n]):
            factor = gene.to_factor()
            factor.name = f"EVOLVED_{i+1:02d}"
            factor.code = f"evolved_{i+1:02d}"
            factors.append(factor)
        return factors


# ==================== 便捷函数 ====================

def evolve_factors(base_factors: List[str], 
                   factor_data: Optional[pd.DataFrame] = None,
                   config: Optional[Dict[str, Any]] = None,
                   seed: Optional[int] = None) -> Tuple[List[Factor], Dict[str, Any]]:
    """
    便捷函数: 进化因子
    
    Args:
        base_factors: 基础因子列表
        factor_data: 因子数据
        config: 配置
        seed: 随机种子
        
    Returns:
        (进化后的Factor列表, 进化结果详情)
    """
    evolver = GeneticFactorEvolution(config)
    result = evolver.evolve(base_factors, factor_data, seed)
    factors = evolver.get_best_factors(n=config.get('top_n', 5) if config else 5)
    return factors, result


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'population_size': 20,
        'generations': 10,
        'mutation_rate': 0.3,
        'crossover_rate': 0.7,
        'target_ic': 0.05
    }
    
    base_factors = ["macd_dif", "kdj_k", "rsi_6", "bb_width", "volume_ratio"]
    
    evolver = GeneticFactorEvolution(config)
    result = evolver.evolve(base_factors, seed=42)
    
    print(f"\n进化完成!")
    print(f"最佳适应度: {result['best_fitness']:.4f}")
    best_ic = result['best_ic'] if result['best_ic'] is not None else 0.0
    print(f"最佳IC: {best_ic:.4f}")
    print(f"完成代数: {result['generations_completed']}")
    
    best_factors = evolver.get_best_factors(n=3)
    print(f"\n最佳因子:")
    for factor in best_factors:
        ic_str = f"{factor.ic_value:.4f}" if factor.ic_value is not None else "N/A"
        print(f"  - {factor.code}: {factor.formula} (IC={ic_str})")
