import { Team } from "../utils/api";

interface Props {
  teams: Team[];
  teamId: number | null;
  onChange: (id: number) => void;
}

const TeamSelector = ({ teams, teamId, onChange }: Props) => (
  <>
    <label htmlFor="team">Team</label>
    <select
      id="team"
      value={teamId ?? ""}
      onChange={(e) => onChange(Number(e.target.value))}
    >
      {teams.map((t) => (
        <option key={t.id} value={t.id}>
          {t.name}
        </option>
      ))}
    </select>
  </>
);

export default TeamSelector;
