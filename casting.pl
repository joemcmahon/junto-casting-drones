#!/usr/bin/perl
use strict;
use warnings;
use List::Util qw(shuffle);
use Getopt::Long;

my ($MAXMINUTES, $TIMESTEP, $drone, @scale);
my @default_scale = qw(A B C D E F G);
my $default_drone = "A1";
GetOptions(
  'end=n'   => \$MAXMINUTES,
  'delay=n' => \$TIMESTEP,
  'drone=s' => \$drone,
  'scale=s' => \@scale,
);

@scale = split(/,/,join(',',@scale));
@scale = @default_scale unless @scale;
$drone = $default_drone unless $drone;

$MAXMINUTES //= 61;
$TIMESTEP   //= 0;
$TIMESTEP   = 60 if $TIMESTEP > 60;
$MAXMINUTES = 99 if $TIMESTEP > 99;

my $minute = 0;
my @notes  = ();
my $step  = 1;
my @steps = (1,1,2,2,2,3);
my $action = 0;
my $now = 0;

sub notesort {
  my(@notes) = @_;
  @notes = map { /^(.*)(.)$/ } @notes;
  # now note octave note octave
  return -1 if $notes[1] < $notes[3];
  return 1 if $notes[1] > $notes[3];
  return -1 if $notes[0] lt $notes[2];
  return 1; # Must be because identical notes are not permitted
}

sub tickformat {
  my ($n) = @_;
  return sprintf("%02d:00 ", $n);
}

print tickformat($now), "fade in\n";
for (my $i = 1; $i <= 61; $i += $step) {
  my $step = $steps[int(rand()*6)];
  if ($step + $now > $MAXMINUTES) {
    $step = $MAXMINUTES - $now;
  }
  print tickformat($now), "Playing $drone (drone) + ", (@notes ? "@{[sort {notesort($a, $b)} @notes]}" : "nothing");
  print " for $step minute@{[$step == 1 ? '' : 's']}\n";
  $now += $step;
  last if $now == $MAXMINUTES;
  sleep $step * $TIMESTEP ;
  my $valid;
  while (not $valid){
    my $action = int(rand()*6)+1;
    $valid++
      if $action < 5
        or $action == 5 && @notes > 1
        or $action == 6 && @notes > 2;
    next unless $valid;
    for ($action) {
      /[1234]/ and add_or_change_notes($_,\$step, \@notes);
      /5/      and drop_one_note(\@notes);
      /6/      and drop_two_notes(\@notes);
    }
  }
}
print tickformat($MAXMINUTES), "fade out\n";
exit 0;

sub drop_a_note {
  my($notes_ref) = @_;
  my $dropped = shift @$notes_ref;
  return $dropped;
}

sub drop_one_note {
  my($notes_ref) = @_;
  my $dropped = drop_a_note($notes_ref);
  print "      Drop one note: $dropped\n";
}

sub drop_two_notes {
  my($notes_ref) = @_;
  my @dropped;
  for (1..2) {
    push @dropped, drop_a_note($notes_ref);
  }
  print "      Drop two notes: ", join(" and ", @dropped), "\n";
}

sub add_or_change_notes {
  my($new, $step_ref, $notes_ref) = @_;
  # If we have fewer than the number of notes proposed, add one.
  if ($new > @$notes_ref) {
    print "      Add $new notes: ";
    my @more;
    for my $j (1..$new){
      (my $add, @$notes_ref) = add_note($notes_ref, @scale);
      push @more, $add;
    }
    print "@{[sort { notesort($a,$b) } @more]}";
  } else {
    # If we have the same number or more, change that many notes.
    print "      Change $new notes:";
    for my $j (1..$new) {
      (my $delta, my $dropped, @$notes_ref) = change_note($notes_ref, @scale);
      print " $delta (drop $dropped)";
    }
  }
  print "\n";
}

sub add_note {
  my($notes_ref, @scale) = @_;
  my %unused;
  for my $octave (3..5) {
    for my $note (@scale) {
      $unused{"$note$octave"} = 1;
    }
  }
  for my $note (@$notes_ref) {
    delete $unused{$note};
  }
  # Choose random unused note
  my $new = (shuffle keys %unused)[0];
  return ($new, @$notes_ref, $new);
}

sub change_note {
  my($notes_ref, @scale) = @_;
  my($new, @added) = add_note($notes_ref, @scale);
  my $dropped = shift @added;
  return($new, $dropped, @added);
}
