from cc3d.core.PySteppables import SteppableBasePy
import os
import inspect
import time
import platform
import numpy as np
import math
import random

import parameters as p

# Sementes fixas para reprodutibilidade
random.seed(12345)
np.random.seed(12345)


class ShortRunBenchmarkSteppable(SteppableBasePy):
    """Benchmark curto com aquecimento por irradiações iniciais.

    Ignora os tempos até completar BENCHMARK_WARMUP_IRRADIATIONS eventos e
    mede uma janela adicional de BENCHMARK_MCS MCS. A duração entre chamadas
    inclui o custo do MCS e dos steppables executados nesse intervalo.
    """

    def __init__(self, frequency=1, max_benchmark_mcs=None):
        SteppableBasePy.__init__(self, frequency)
        self.measure_mcs = int(
            max_benchmark_mcs if max_benchmark_mcs is not None
            else getattr(p, "BENCHMARK_MCS", 250)
        )
        self.warmup_irradiations = max(0, int(getattr(p, "BENCHMARK_WARMUP_IRRADIATIONS", 5)))
        interval = int(p.MCS_Between_Ions)
        first_event = int(math.ceil(p.Relax_Time / interval) * interval)
        self.warmup_end_mcs = first_event + max(0, self.warmup_irradiations - 1) * interval
        self.measure_end_mcs = self.warmup_end_mcs + self.measure_mcs
        self.last_time = None
        self.started_at = None
        self.mcs_samples = []  # (mcs, segundos desde a chamada anterior), só janela medida
        self.finished = False

    def start(self):
        self.started_at = time.perf_counter()
        self.last_time = self.started_at

    @staticmethod
    def is_irradiation_mcs(mcs):
        return mcs >= p.Relax_Time and mcs % p.MCS_Between_Ions == 0

    def step(self, mcs):
        if self.finished:
            return
        now = time.perf_counter()
        dt = max(0.0, now - self.last_time) if self.last_time is not None else 0.0
        self.last_time = now

        # O aquecimento termina no MCS da quinta irradiação (por padrão, 200).
        # A janela medida começa no MCS seguinte e dura BENCHMARK_MCS MCS.
        if self.warmup_end_mcs < int(mcs) <= self.measure_end_mcs:
            self.mcs_samples.append((int(mcs), dt))

        if int(mcs) < self.measure_end_mcs:
            return

        self.finished = True
        elapsed = max(0.0, now - self.started_at)
        samples = self.mcs_samples
        event_times = [dt for step_mcs, dt in samples if self.is_irradiation_mcs(step_mcs)]
        regular_times = [dt for step_mcs, dt in samples if not self.is_irradiation_mcs(step_mcs)]
        avg_event = float(np.mean(event_times)) if event_times else None
        avg_regular = float(np.mean(regular_times)) if regular_times else None
        avg_all = float(np.mean([dt for _, dt in samples])) if samples else 0.0

        total_mcs = int(p.Total_MCS)
        interval = int(p.MCS_Between_Ions)
        first_event_mcs = int(math.ceil(p.Relax_Time / interval) * interval)
        total_events = max(0, (total_mcs - first_event_mcs) // interval + 1)
        events_occurred_by_now = max(0, (int(mcs) - first_event_mcs) // interval + 1) if int(mcs) >= first_event_mcs else 0
        remaining_mcs = max(0, total_mcs - int(mcs))
        remaining_events = max(0, total_events - events_occurred_by_now)
        remaining_regular = max(0, remaining_mcs - remaining_events)

        if avg_event is not None and avg_regular is not None:
            remaining_seconds = remaining_events * avg_event + remaining_regular * avg_regular
            method = "médias da janela pós-aquecimento, separando MCS com evento e comuns"
        else:
            remaining_seconds = remaining_mcs * avg_all
            method = "média global da janela pós-aquecimento (classes insuficientes)"
        projected_seconds = elapsed + remaining_seconds

        def fmt_duration(seconds):
            seconds = max(0, int(round(seconds)))
            days, rem = divmod(seconds, 86400)
            hours, rem = divmod(rem, 3600)
            minutes, secs = divmod(rem, 60)
            if days:
                return f"{days} d {hours:02d} h {minutes:02d} min"
            return f"{hours:02d} h {minutes:02d} min {secs:02d} s"

        with open("benchmark_results.txt", "w", encoding="utf-8") as f:
            f.write("=== BENCHMARK CURTO COM AQUECIMENTO E PROJEÇÃO ===\n")
            f.write(f"Sistema: {platform.platform()}\n")
            f.write(f"Irradiações ignoradas no aquecimento: {self.warmup_irradiations}\n")
            f.write(f"Aquecimento concluído no MCS: {self.warmup_end_mcs}\n")
            f.write(f"Janela medida: MCS {self.warmup_end_mcs + 1} a {self.measure_end_mcs} ({len(samples)} amostras)\n")
            f.write(f"Tempo decorrido incluindo aquecimento: {fmt_duration(elapsed)} ({elapsed:.2f} s)\n")
            f.write(f"MCS totais configurados: {total_mcs}\n")
            f.write(f"Eventos previstos pela condição de Nucleation.step: {total_events}\n")
            f.write(f"Eventos já ocorridos até o fim do benchmark: {events_occurred_by_now}\n")
            f.write(f"Eventos medidos na janela: {len(event_times)}\n")
            f.write(f"Eventos restantes estimados: {remaining_events}\n")
            f.write(f"Método de projeção: {method}\n\n")
            f.write(f"Média por MCS (janela): {avg_all * 1000:.3f} ms\n")
            f.write(f"Média por MCS comum: {np.mean(regular_times) * 1000:.3f} ms\n" if regular_times else "Média por MCS comum: indisponível\n")
            f.write(f"Média por MCS com evento: {np.mean(event_times) * 1000:.3f} ms\n" if event_times else "Média por MCS com evento: indisponível\n")
            f.write(f"Tempo restante estimado: {fmt_duration(remaining_seconds)} ({remaining_seconds / 3600:.2f} h)\n")
            f.write(f"TEMPO TOTAL ESTIMADO: {fmt_duration(projected_seconds)} ({projected_seconds / 3600:.2f} h)\n\n")
            f.write("AVISO: extrapolação baseada numa janela curta; o custo pode mudar com a evolução da microestrutura.\n")
            f.write("Use a mesma máquina, parâmetros e seed ao comparar versões do código.\n")

        print("\n[BENCHMARK CONCLUÍDO] Relatório salvo em 'benchmark_results.txt'.")
        print(f"[BENCHMARK] Aquecimento até MCS {self.warmup_end_mcs}; medição até MCS {self.measure_end_mcs}.")
        print(f"[BENCHMARK] Tempo total estimado: {fmt_duration(projected_seconds)}")
        self.stop_simulation()


class FilmSetup(SteppableBasePy):

  def __init__(self, frequency=1):
    SteppableBasePy.__init__(self, frequency)

  def start(self):
    import parameters as p

    for cell in self.cell_list_by_type(self.MATERIAL):
      cell.targetVolume = p.Material_TargetVolume
      cell.lambdaVolume = p.Material_LambdaVolume_Cold


class Nucleation(SteppableBasePy):

  def __init__(self, frequency=1):
    SteppableBasePy.__init__(self, frequency)
    self.time = time.strftime("%Y_%m_%d_at_%Hh_%Mm_%Ss")
    output_dir = "C:\\CompuCell3D\\CC3DWorkspace\\Results\\" + self.time
    self.set_output_dir(output_dir, abs_path=False)
    self.Height_Now = p.Initial_Sample_Height

  def start(self):
    import parameters as p

    SourceDir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    Dir = SourceDir + "\\Results"
    self.set_output_dir(output_dir=Dir + "\\" + self.time, abs_path=False)
    grid = self.dim.x

    fluency = "{:.2e}".format(p.Fluency)
    dimbound = "3DPBC"
    Name = (
        dimbound
        + "_F"
        + str(fluency)
        + "_H"
        + str(p.Initial_Sample_Height)
        + "_G"
        + str(grid)
        + "_IR"
        + str(p.Ion_Radius)
    )

    self.routinetrkName = Dir + "\\" + self.time + "_routinetrk_" + Name + ".dat"
    file = open(self.routinetrkName, "w")
    file.write("%s\n" % ("mcs NM NG MV GV "))
    file.close()

    self.creationtrkName = (
        Dir + "\\" + self.time + "_creationtrk_" + Name + ".dat"
    )
    file = open(self.creationtrkName, "w")
    file.write("mcs PoreIndex PoreX PoreY PoreZ\n")
    file.close()

    self.htrkName = Dir + "\\" + self.time + "_htrk_" + Name + ".dat"
    file = open(self.htrkName, "w")
    file.write("%s\n" % ("mcs H "))
    file.close()

    self.randtrkName = Dir + "\\" + self.time + "_randtrk_" + Name + ".dat"
    file = open(self.randtrkName, "w")
    file.write("%s\n" % ("mcs RandX RandY RandZ "))
    file.close()

    self.ellipsetrkName = Dir + "\\" + self.time + "_ellipsetrk_" + Name + ".dat"
    file = open(self.ellipsetrkName, "w")
    file.write(
        "%s\n"
        % ("PoreID PoreVol MajorAx MinorAx MedianAx PoreX PoreY PoreZ")
    )
    file.close()

    self.simparamName = Dir + "\\" + self.time + "_simparam_" + Name + ".dat"
    file = open(self.simparamName, "w")
    file.write("%s\n" % ("Simulation Parameters "))
    file.close()

    self.layerstrkName = Dir + "\\" + self.time + "_layerstrk_" + Name + ".dat"
    file = open(self.layerstrkName, "w")
    file.write("%s\n" % ("mcs L0P L0V L1P L1V L2P L2V L3P L3V"))
    file.close()

    # Gráficos no player
    self.pW1 = self.add_new_plot_window(
        title="Number of Cells",
        x_axis_title="MCS",
        y_axis_title="Counts",
        x_scale_type="linear",
        y_scale_type="linear",
        grid=True,
    )
    self.pW1.add_plot("Mat", style="Dots", color="blue", size=5)
    self.pW1.add_plot("Pore", style="Dots", color="green", size=5)

    self.pW2 = self.add_new_plot_window(
        title="Total Volumes",
        x_axis_title="MCS",
        y_axis_title="nm³",
        x_scale_type="linear",
        y_scale_type="linear",
        grid=True,
    )
    self.pW2.add_plot("Mat", style="Dots", color="blue", size=5)
    self.pW2.add_plot("Pore", style="Dots", color="green", size=5)

    self.pW3 = self.add_new_plot_window(
        title="Height",
        x_axis_title="MCS",
        y_axis_title="h",
        x_scale_type="linear",
        y_scale_type="linear",
        grid=True,
    )
    self.pW3.add_plot("H", style="Lines", color="red", size=5)

  def in_circle(
      self, x, y, radius, center_x, center_y, lattice_x, lattice_y
  ):
    dx = min(abs(center_x - x), center_x + lattice_x - x)
    dy = min(abs(center_y - y), center_y + lattice_y - y)
    distance2 = round(dx**2 + dy**2)
    return distance2 <= (radius**2)

  def in_sphere(
      self,
      x,
      y,
      z,
      radius,
      center_x,
      center_y,
      center_z,
      lattice_x,
      lattice_y,
  ):
    dx = min(abs(center_x - x), center_x + lattice_x - x)
    dy = min(abs(center_y - y), center_y + lattice_y - y)
    dz = abs(center_z - z)
    distance2 = round(dx**2 + dy**2 + dz**2)
    return distance2 <= (radius**2)

  def outputs(self):
    return

  def step(self, mcs):
    import parameters as p

    if mcs % 500 == 0:
      Material_Counter = 0
      Material_Volume = 0
      Pore_Counter = 0
      Pore_Volume = 0

      for cell in self.cell_list:
        if cell.type == self.MATERIAL:
          Material_Counter += 1
          Material_Volume += cell.volume
        if cell.type == self.PORE:
          Pore_Counter += 1
          Pore_Volume += cell.volume

      self.pW1.add_data_point("Mat", mcs, Material_Counter)
      self.pW1.add_data_point("Pore", mcs, Pore_Counter)
      self.pW2.add_data_point("Mat", mcs, Material_Volume)
      self.pW2.add_data_point("Pore", mcs, Pore_Volume)

      file = open(self.routinetrkName, "a")
      file.write(
          "%d %d %d %.2f %.2f\n"
          % (
              mcs,
              Material_Counter,
              Pore_Counter,
              Material_Volume,
              Pore_Volume,
          )
      )
      file.close()

    if (mcs >= p.Relax_Time) and (mcs % p.MCS_Between_Ions == 0):
      file = open(self.htrkName, "a")
      file.write("%d %d\n" % (mcs, self.Height_Now))
      file.close()

      self.pW3.add_data_point("H", mcs, self.Height_Now)

      # Cooling all cells (Corrigido para self.PORE e self.MATERIAL)
      for cell in self.cell_list:
        cell.fluctAmpl = p.Temperature_Cold
        if cell.type == self.PORE:
          cell.lambdaVolume = p.Pore_LambdaVolume_Cold
        if cell.type == self.MATERIAL:
          cell.lambdaVolume = p.Material_LambdaVolume_Cold

      # Chooses XY for ion track
      Ion_X = random.randint(1, self.dim.x)
      Ion_Y = random.randint(1, self.dim.y)

      active_limit_z = min(self.dim.z, self.Height_Now + int(p.Ion_Radius))

      # Heating cylinder cells (com varredura restrita ao topo dinâmico)
      for k in range(1, active_limit_z):
        for i in range(
            int(Ion_X - p.Ion_Radius), int(Ion_X + p.Ion_Radius + 1)
        ):
          if i < 1:
            i += p.Lx
          if i > p.Lx:
            i -= p.Lx
          for j in range(
              int(Ion_Y - p.Ion_Radius), int(Ion_Y + p.Ion_Radius + 1)
          ):
            if j < 1:
              j += p.Ly
            if j > p.Ly:
              j -= p.Ly
            if self.in_circle(i, j, p.Ion_Radius, Ion_X, Ion_Y, p.Lx, p.Ly):
              cell = self.cell_field[i, j, k]
              if cell:
                cell.fluctAmpl = p.Temperature_Hot
                if cell.type == self.MATERIAL:
                  cell.lambdaVolume = p.Material_LambdaVolume_Hot
                if cell.type == self.PORE:
                  cell.lambdaVolume = p.Pore_LambdaVolume_Hot

      # All pore creation logic
      Creation_Counter = 0
      for Pore in range(p.Pore_Max_Number):
        while 1:
          Random_Radius = random.random() * p.Ion_Radius
          Random_Theta = 2 * np.pi * random.random()
          Random_X = Ion_X + Random_Radius * math.cos(Random_Theta)
          if Random_X < 1:
            Random_X += p.Lx
          if Random_X > p.Lx:
            Random_X -= p.Lx
          Random_Y = Ion_Y + Random_Radius * math.sin(Random_Theta)
          if Random_Y < 1:
            Random_Y += p.Ly
          if Random_Y > p.Ly:
            Random_Y -= p.Ly
          Random_Z = random.randint(1, self.Height_Now)
          Current_Cell = self.cell_field[Random_X, Random_Y, Random_Z]
          if Current_Cell:
            if Current_Cell.type == self.MATERIAL:
              break

        Near_Pore_Cells = set()
        for k in range(
            max(1, int(Random_Z - p.Ion_Radius)),
            int(Random_Z + p.Ion_Radius + 1),
        ):
          for i in range(
              int(Ion_X - p.Ion_Radius), int(Ion_X + p.Ion_Radius + 1)
          ):
            if i < 1:
              i += p.Lx
            if i > p.Lx:
              i -= p.Lx
            for j in range(
                int(Ion_Y - p.Ion_Radius), int(Ion_Y + p.Ion_Radius + 1)
            ):
              if j < 1:
                j += p.Ly
              if j > p.Ly:
                j -= p.Ly
              if self.in_circle(i, j, p.Ion_Radius, Ion_X, Ion_Y, p.Lx, p.Ly):
                cell = self.cell_field[i, j, k]
                if cell:
                  if cell.type == self.PORE:
                    Near_Pore_Cells.add(cell.id)

        if len(Near_Pore_Cells) != 0:
          for index in Near_Pore_Cells:
            cell = self.fetch_cell_by_id(index)
            cell.targetVolume += p.Pore_TargetVolume / len(Near_Pore_Cells)

        else:
          Current_Cell.lambdaVolume = 50.0
          New_Cell = self.new_cell(self.PORE)
          self.cell_field[Random_X, Random_Y, Random_Z] = New_Cell
          New_Cell.targetVolume = p.Pore_TargetVolume
          New_Cell.lambdaVolume = p.Pore_LambdaVolume_Hot
          Creation_Counter += 1

          if Random_Z > self.Height_Now:
            self.Height_Now = int(Random_Z)

          file = open(self.creationtrkName, "a")
          file.write(
              "%d %d %d %d %d\n"
              % (
                  mcs,
                  Creation_Counter,
                  int(Random_X),
                  int(Random_Y),
                  int(Random_Z),
              )
          )
          file.close()

  def finish(self):
    with open(self.ellipsetrkName, "a") as file:
      for cell in self.cell_list:
        if cell.type == self.PORE:
          axes = self.momentOfInertiaPlugin.getSemiaxes(cell)
          file.write(
            "%d %d %.2f %.2f %.2f %d %d %d\n"
            % (
                cell.id,
                cell.volume,
                axes[2],
                axes[0],
                axes[1],
                cell.xCOM,
                cell.yCOM,
                cell.zCOM,
            )
          )

  def on_stop(self):
    pass