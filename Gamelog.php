<?php
        $con = mysqli_connect("localhost", "jcsuser", "jcspassword", "JCS");
        if(mysqli_connect_errno()) echo "Failed to connect to MySQL: " . mysqli_connect_errno();
 	// connect to database

	function DisplayGamelog($year = NULL, $team = NULL) {
                global $con;

		echo "<table class=\"tablesorter\" id=\"gamelog\" border='1'>";
		echo "<thead><tr>";

		echo "<th>Date</th>";

		echo "<th>Away</th>";
		echo "<th>Score</th>";
		echo "<th>PassYds</th>";
		echo "<th>PassCmp</th>";
		echo "<th>PassAtt</th>";
		echo "<th>RushYds</th>";
		echo "<th>RushAtt</th>";
		echo "<th>Ints</th>";
		echo "<th>Fumbs</th>";
		echo "<th>FirstDowns</th>";
		echo "<th>Penalties</th>";
		echo "<th>PenYds</th>";

		echo "<th>Home</th>";
		echo "<th>Line</th>";
		echo "<th>Score</th>";
		echo "<th>PassYds</th>";
		echo "<th>PassCmp</th>";
		echo "<th>PassAtt</th>";
		echo "<th>RushYds</th>";
		echo "<th>RushAtt</th>";
		echo "<th>Ints</th>";
		echo "<th>Fumbs</th>";
		echo "<th>FirstDowns</th>";
		echo "<th>Penalties</th>";
		echo "<th>PenYds</th>";


		echo "</tr></thead>";
		echo "<tbody>";

		$games = mysqli_query($con, "select away.name, home.name, game.*, away.id, home.id from Games as game inner join Teams as home on home.id = game.homeTeamID inner join Teams as away on away.id = game.awayTeamID where game.date > '" . $year . "-07-01'  and game.date < '" . ($year + 1) . "-07-01' order by game.date");
		while($game = mysqli_fetch_array($games)) {
			if($team != 0)
				if($game[31] != $team && $game[30] != $team)
					continue;
			// skip if not the team we want

			echo "<tr>";
			echo "<td>" . $game[3] . "</td>";

			$td = "<td style='background-color:rgba(255,0,0,.25)'>";
			echo $td . $game[0] . "</td>";
			echo $td . $game[5] . "</td>";
			echo $td . $game[6] . "</td>";
			echo $td . $game[8] . "</td>";
			echo $td . $game[7] . "</td>";
			echo $td . $game[9] . "</td>";
			echo $td . $game[10] . "</td>";
			echo $td . $game[11] . "</td>";
			echo $td . $game[12] . "</td>";
			echo $td . $game[13] . "</td>";
			echo $td . $game[14] . "</td>";
			echo $td . $game[15] . "</td>";

			$td = "<td style='background-color:rgba(0,0,255,.25)'>";
			echo $td . $game[1] . "</td>";
			echo $td . $game[28] . "</td>";
			echo $td . $game[17] . "</td>";
			echo $td . $game[18] . "</td>";
			echo $td . $game[20] . "</td>";
			echo $td . $game[19] . "</td>";
			echo $td . $game[21] . "</td>";
			echo $td . $game[22] . "</td>";
			echo $td . $game[23] . "</td>";
			echo $td . $game[24] . "</td>";
			echo $td . $game[25] . "</td>";
			echo $td . $game[26] . "</td>";
			echo $td . $game[27] . "</td>";

			echo "</tr>";
		}

		echo "</tbody>";
		echo "</table>";
	}
?>

<html><body>
<!-- <link href="Gamelog.css" rel="stylesheet"> -->
<script type="text/javascript" src="jquery-1.4.2.min.js"></script>
<script type="text/javascript" src="jquery.tablesorter.js"></script>
<script type="text/javascript">
	$(document).ready(function() {
		$("#gamelog").tablesorter({
			sortList:[[0,0]],
			sortRestart:true,
			headers: {
				0:  {sortInitialOrder:'asc'},
				1:  {sortInitialOrder:'asc'},
				2:  {sortInitialOrder:'desc'},
				3:  {sortInitialOrder:'desc'},
				4:  {sortInitialOrder:'desc'},
				5:  {sortInitialOrder:'desc'},
				6:  {sortInitialOrder:'desc'},
				7:  {sortInitialOrder:'desc'},
				8:  {sortInitialOrder:'desc'},
				9:  {sortInitialOrder:'desc'},
				10: {sortInitialOrder:'desc'},
				11: {sortInitialOrder:'desc'},
				12: {sortInitialOrder:'desc'},
				13: {sortInitialOrder:'asc'},
				14: {sortInitialOrder:'asc'},
				15: {sortInitialOrder:'desc'},
				16: {sortInitialOrder:'desc'},
				17: {sortInitialOrder:'desc'},
				18: {sortInitialOrder:'desc'},
				19: {sortInitialOrder:'desc'},
				20: {sortInitialOrder:'desc'},
				21: {sortInitialOrder:'desc'},
				22: {sortInitialOrder:'desc'},
				23: {sortInitialOrder:'desc'},
				24: {sortInitialOrder:'desc'},
				25: {sortInitialOrder:'desc'},
				26: {sortInitialOrder:'desc'},
			},
		});
	});

     	function setDropdowns($year, $team) {
   	        $("#yearselect option").each(function() {
                        if($(this).attr("value") == $year) $(this).parent().attr("selectedIndex", $(this).index());
    		});

		$("#teamselect option").each(function() {
			if($(this).attr("value") == $team) $(this).parent().attr("selectedIndex", $(this).index());
		});
       	}
</script>

<div id="filters"><form method="POST">
	<select id="yearselect" name="year">
<?php
		for($i = 2017; $i >= 1978; $i--) {
			echo "<option value='" . $i . "'>" . $i . "</option>";
		}
?>
	</select>
	<select id="teamselect" name="team">
		<option value="0">ALL TEAMS</option>
<?php
		$teams = mysqli_query($con, "select * from Teams order by Teams.name");
		while($team = mysqli_fetch_array($teams)) {
			echo "<option value='" . $team[0] . "'>" . $team[1] . "</option>";
		}
?>
	</select>
	<input type="submit" value="Search">
</form></div>

<div id="games">
<?php
	$myyear = 2017;
	$myteam = 0;
	if(isset($_POST['year']))
		$myyear = $_POST['year'];
	if(isset($_POST['team']))
		$myteam = $_POST['team'];

	DisplayGameLog($myyear, $myteam);
        echo "<script type='text/javascript'>setDropdowns(" . $myyear . ", " . $myteam . ");</script>";
?>
</div>
</body></html>
